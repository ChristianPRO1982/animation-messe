from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class EmailSettings(models.Model):
    id = models.PositiveSmallIntegerField(primary_key=True, default=1, editable=False)
    enabled = models.BooleanField(default=False)

    class Meta:
        db_table = 'am"."e_email_settings'
        constraints = [
            models.CheckConstraint(
                condition=models.Q(id=1), name="email_settings_singleton"
            )
        ]


class EmailNotification(models.Model):
    STATUS_PENDING = "pending"
    STATUS_SENT = "sent"
    STATUS_FAILED = "failed"
    STATUS_SKIPPED = "skipped"
    STATUS_BLOCKED_ENV = "blocked_env"
    STATUS_BLOCKED_ADMIN = "blocked_admin"
    STATUS_BLOCKED_ADMIN_HISTORY = "blocked_admin_history"
    STATUS_CHOICES = (
        (STATUS_PENDING, _("En attente")),
        (STATUS_SENT, _("Envoyé")),
        (STATUS_FAILED, _("Échec")),
        (STATUS_SKIPPED, _("Ignoré")),
        (STATUS_BLOCKED_ENV, _("Blocage environnement")),
        (STATUS_BLOCKED_ADMIN, _("Blocage administratif courant")),
        (STATUS_BLOCKED_ADMIN_HISTORY, _("Blocage administratif historique")),
    )
    SENDER_CHOICES = (("default", _("Notifications")), ("planning", _("Planning")))

    een_id = models.BigAutoField(primary_key=True)
    notification_type = models.CharField(max_length=100)
    sender_key = models.CharField(
        max_length=32, choices=SENDER_CHOICES, default="default"
    )
    recipient_email = models.EmailField(max_length=254)
    recipient_member_id = models.UUIDField(blank=True, null=True)
    group = models.ForeignKey(
        "app_group.Group",
        blank=True,
        db_column="gg_id",
        null=True,
        on_delete=models.SET_NULL,
        related_name="email_notifications",
    )
    content_object_type = models.CharField(max_length=255, blank=True)
    content_object_id = models.CharField(max_length=255, blank=True)
    business_key = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        unique=True,
    )
    status = models.CharField(
        max_length=32,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
    )
    provider_message_id = models.CharField(max_length=255, blank=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(blank=True, null=True)
    failed_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'am"."e_email_notification'
        indexes = [
            models.Index(
                fields=["notification_type", "status"],
                name="een_type_status_idx",
            ),
            models.Index(
                fields=["status", "created_at"], name="een_status_created_idx"
            ),
            models.Index(fields=["group", "status"], name="een_group_status_idx"),
        ]
        ordering = ["-created_at", "-een_id"]

    def __str__(self) -> str:
        return f"{self.notification_type} -> {self.recipient_email}"

    def mark_sent(self, *, provider_message_id: str = "", now=None) -> None:
        self.status = self.STATUS_SENT
        self.provider_message_id = str(provider_message_id or "")[:255]
        self.error_message = ""
        self.sent_at = now or timezone.now()
        self.failed_at = None
        self.save(
            update_fields=[
                "status",
                "provider_message_id",
                "error_message",
                "sent_at",
                "failed_at",
                "updated_at",
            ]
        )

    def mark_failed(self, error_message: str, *, now=None) -> None:
        self.status = self.STATUS_FAILED
        self.error_message = str(error_message or "")[:1000]
        self.failed_at = now or timezone.now()
        self.save(
            update_fields=[
                "status",
                "error_message",
                "failed_at",
                "updated_at",
            ]
        )

    def mark_skipped(self, reason: str, *, now=None) -> None:
        self.status = self.STATUS_SKIPPED
        self.error_message = str(reason or "")[:1000]
        self.failed_at = now or timezone.now()
        self.save(
            update_fields=[
                "status",
                "error_message",
                "failed_at",
                "updated_at",
            ]
        )

    def mark_blocked(self, status: str) -> None:
        reasons = {
            self.STATUS_BLOCKED_ENV: _("Impossible d'envoyer des emails"),
            self.STATUS_BLOCKED_ADMIN: _(
                "Impossible d'envoyer des emails - blocage administratif"
            ),
        }
        self.error_message = str(reasons[status])
        self.status = status
        self.failed_at = None
        self.save(update_fields=["status", "error_message", "failed_at", "updated_at"])
