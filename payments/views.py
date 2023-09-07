import stripe
import datetime

from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.timezone import make_aware


from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)


from authentication.middleware import CustomAuthentication
from payments.models import Customer
from payments.tasks import del_customer_task
from authentication.models import User
from payments.utils import get_subscription_info


stripe.api_key = settings.STRIPE_SECRET_KEY
STRIPE_WEBHOOK_SECRET = settings.STRIPE_WEBHOOK_SECRET
STRIPE_BASIC_PRICE_ID = settings.STRIPE_BASIC_PRICE_ID
STRIPE_PRO_PRICE_ID = settings.STRIPE_PRO_PRICE_ID
STRIPE_ADDON_PRICE_ID = settings.STRIPE_ADDON_PRICE_ID


@api_view(["GET"])
@authentication_classes([CustomAuthentication])
@permission_classes([IsAuthenticated])
def check_subscription_view(request):
    payload = get_subscription_info(request.user)
    return JsonResponse(
        {"detail": "Subscription details", "payload": payload},
        status=status.HTTP_200_OK,
    )


@csrf_exempt
def webhook(request):
    # Retrieve the poll by verifying the signature using the raw body and secret if webhook signing is configured.
    try:
        signature = request.headers["STRIPE_SIGNATURE"]
        event = stripe.Webhook.construct_event(
            payload=request.body, sig_header=signature, secret=STRIPE_WEBHOOK_SECRET
        )
        # Get the type of webhook poll sent - used to check the status of PaymentIntents.
        poll_type = event.type
        data = event.data.object

        print("poll_type: {}".format(poll_type))

    except Exception:
        return HttpResponse(status=400)

    if poll_type == "payment_intent.succeeded":
        print(data)

        # price_id = None
        # if price_id == STRIPE_ADDON_PRICE_ID:
        #     quantity = payment.metadata["quantity"]
        #     customer_id = payment.customer
        #     try:
        #         customer_instance = Customer.objects.get(stripe_customer_id=customer_id)
        #         customer_instance.credit_minutes += quantity*60
        #         customer_instance.save(update_fields=["credit_minutes"])
        #     except Customer.DoesNotExist:
        #         del_customer_task.delay(customer_id)

    elif poll_type == "customer.subscription.updated" and data.status == "active":
        price_id = data.plan.id
        if price_id in [STRIPE_BASIC_PRICE_ID, STRIPE_PRO_PRICE_ID]:
            subscription_id = data.id
            customer_id = data.customer
            current_period_end = data.current_period_end
            cancel_at_period_end = data.cancel_at_period_end
            try:
                stripe_customer = stripe.Customer.retrieve(customer_id)
                user = User.objects.get(email=stripe_customer.email)
                credit_minutes = 0
                if price_id == STRIPE_BASIC_PRICE_ID:
                    credit_minutes = 12 * 60
                elif price_id == STRIPE_PRO_PRICE_ID:
                    credit_minutes = 36 * 60

                Customer.objects.update_or_create(
                    user=user,
                    defaults={
                        "stripe_customer_id": customer_id,
                        "stripe_subscription_id": subscription_id,
                        "current_period_end": make_aware(
                            datetime.datetime.fromtimestamp(current_period_end)
                        ),
                        "cancel_at_period_end": cancel_at_period_end,
                        "credit_minutes": credit_minutes,
                        "plan": Customer.BASIC
                        if price_id == STRIPE_BASIC_PRICE_ID
                        else Customer.PRO,
                    },
                )
            except (Customer.DoesNotExist, User.DoesNotExist):
                del_customer_task.delay(customer_id)

    elif poll_type == "customer.subscription.deleted":
        try:
            subscription_id = data.id
            customer_id = data.customer
            customer_instance = Customer.objects.get(
                stripe_subscription_id=subscription_id
            )
            customer_instance.cancel_at_period_end = True
            customer_instance.save(update_fields=["cancel_at_period_end"])
        except Customer.DoesNotExist:
            pass
    else:
        print("Unhandled poll type {}".format(poll_type))

    return HttpResponse(status=200)
