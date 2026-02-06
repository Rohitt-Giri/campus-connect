from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.action(description="Approve selected users")
def approve_users(modeladmin, request, queryset):
    queryset.update(is_approved=True)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("username", "email", "role", "is_approved", "is_staff", "is_superuser")
    list_filter = ("role", "is_approved", "is_staff", "is_superuser")
    search_fields = ("username", "email")
    actions = [approve_users]

    fieldsets = BaseUserAdmin.fieldsets + (
        ("Campus Connect", {"fields": ("role", "is_approved")}),
    )
