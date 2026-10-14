from django.contrib import admin

from app_email.models import EmailNotification
from app_email.services import get_sender_address


@admin.register(EmailNotification)
class EmailNotificationAdmin(admin.ModelAdmin):
    date_hierarchy = "created_at"
    list_display = (
        "een_id",
        "notification_type",
        "sender_key",
        "recipient_email",
        "group",
        "status",
        "created_at",
        "sent_at",
        "failed_at",
    )
    list_filter = (
        "notification_type",
        "sender_key",
        "status",
        "group",
        "created_at",
        "sent_at",
    )
    readonly_fields = (
        "sender_key",
        "sender_address",
        "een_id",
        "notification_type",
        "recipient_email",
        "recipient_member_id",
        "group",
        "content_object_type",
        "content_object_id",
        "business_key",
        "status",
        "provider_message_id",
        "error_message",
        "created_at",
        "sent_at",
        "failed_at",
        "updated_at",
    )
    search_fields = (
        "recipient_email",
        "business_key",
        "error_message",
        "provider_message_id",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.display(description="Expéditeur configuré")
    def sender_address(self, obj):
        return get_sender_address(obj.sender_key)
