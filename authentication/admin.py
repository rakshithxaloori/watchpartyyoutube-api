from django.contrib import admin

from authentication.models import User, Account, Session

admin.site.register(User)
admin.site.register(Account)
admin.site.register(Session)
