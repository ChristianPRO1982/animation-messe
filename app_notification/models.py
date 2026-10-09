from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

EMAIL_STATUS_PENDING = "pending"
EMAIL_STATUS_SENT = "sent"
EMAIL_STATUS_FAILED = "failed"


class EmailNotification(models.Model):
    STATUS_PENDING = EMAIL_STATUS_PENDING
    STATUS_SENT = EMAIL_STATUS_SENT
    STATUS_FAILED = EMAIL_STATUS_FAILED
    STATUS_CHOICES = (
        (STATUS_PENDING, _("En attente")),
        (STATUS_SENT, _("Envoyé")),
        (STATUS_FAILED, _("Échec")),
    )

    en_id = models.BigAutoField(primary_key=True)
    notification_type = models.CharField(max_length=120)
    recipient = models.EmailField()
    group_id = models.IntegerField(blank=True, null=True)
    object_type = models.CharField(max_length=120, blank=True)
    object_id = models.CharField(max_length=120, blank=True)
    idempotency_key = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(
        max_length=16,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
    )
    provider_message_id = models.CharField(max_length=255, blank=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'am"."email_notification'
        ordering = ["-created_at", "-en_id"]
        constraints = [
            models.CheckConstraint(
                condition=Q(
                    status__in=[
                        EMAIL_STATUS_PENDING,
                        EMAIL_STATUS_SENT,
                        EMAIL_STATUS_FAILED,
                    ]
                ),
                name="email_notification_status_valid",
            ),
            models.UniqueConstraint(
                fields=["idempotency_key"],
                condition=Q(idempotency_key__isnull=False),
                name="email_notification_idempotency_unique",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.notification_type} -> {self.recipient} ({self.status})"
