from django.contrib import admin

from app_notification.models import EmailNotification


@admin.register(EmailNotification)
class EmailNotificationAdmin(admin.ModelAdmin):
    list_display = (
        "notification_type",
        "recipient",
        "group_id",
        "status",
        "created_at",
        "sent_at",
    )
    list_filter = ("notification_type", "status", "created_at")
    search_fields = ("recipient", "notification_type", "object_type", "object_id")
    readonly_fields = (
        "notification_type",
        "recipient",
        "group_id",
        "object_type",
        "object_id",
        "idempotency_key",
        "status",
        "provider_message_id",
        "error_message",
        "created_at",
        "sent_at",
        "updated_at",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
