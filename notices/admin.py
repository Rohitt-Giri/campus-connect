from django.contrib import admin
from .models import Notice

@admin.register(Notice)
class NoticeAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "is_active", "created_at", "created_by")
    list_filter = ("category", "is_active")
    search_fields = ("title", "content")
