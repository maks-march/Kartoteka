from django.contrib import admin
from apps.users.domain.models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ("username", "email", "is_staff", "is_active")
    list_filter = ("is_staff", "is_active")
    search_fields = ("username", "email")
