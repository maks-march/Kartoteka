from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

# admin.site.unregister(User)

# @admin.register(User)
# class UserAdmin(BaseUserAdmin):
#     list_display = ["username", "email", "is_staff", "date_joined"]
#     list_filter = ["is_staff", "is_superuser", "date_joined"]
#     search_fields = ["username", "email"]
