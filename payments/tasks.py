import stripe


from watchpartyyoutube.celery import app as celery_app


@celery_app.task(queue="celery")
def del_customer_task(cust_id):
    try:
        stripe.Customer.delete(cust_id)
    except Exception:
        pass


# TODO if current_period_end is passed, make credit_hours 0
