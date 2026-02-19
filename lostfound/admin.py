from django.contrib import admin
from .models import LostFoundItem, ClaimRequest


@admin.register(LostFoundItem)
class LostFoundItemAdmin(admin.ModelAdmin):
    list_display = ("id", "item_type", "title", "status", "created_by", "created_at")
    list_filter = ("item_type", "status")
    search_fields = ("title", "description", "location", "created_by__username")


@admin.register(ClaimRequest)
class ClaimRequestAdmin(admin.ModelAdmin):
    list_display = ("id", "item", "full_name", "phone", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("full_name", "phone", "email", "proof_message", "item__title")
