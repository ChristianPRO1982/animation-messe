from __future__ import annotations

import logging
from dataclasses import dataclass

from django.conf import settings
from django.core.mail import EmailMultiAlternatives, get_connection
from django.template.loader import render_to_string
from django.utils import timezone

from app_notification.models import EmailNotification

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class EmailTemplate:
    subject: str
    body_text: str
    body_html: str


def build_idempotency_key(
    notification_type: str,
    *,
    recipient: str,
    object_type: str = "",
    object_id: str = "",
) -> str:
    normalized_recipient = str(recipient or "").strip().lower()
    return "|".join(
        [
            str(notification_type or "").strip(),
            str(object_type or "").strip(),
            str(object_id or "").strip(),
            normalized_recipient,
        ]
    )


def render_email_template(notification_type: str, context: dict) -> EmailTemplate:
    template_root = f"emails/{notification_type}"
    subject = render_to_string(f"{template_root}/subject.txt", context)
    subject = " ".join(subject.splitlines()).strip()
    body_text = render_to_string(f"{template_root}/body.txt", context)
    body_html = render_to_string(f"{template_root}/body.html", context)
    return EmailTemplate(subject=subject, body_text=body_text, body_html=body_html)


def create_notification(
    *,
    notification_type: str,
    recipient: str,
    group_id: int | None = None,
    object_type: str = "",
    object_id: str | int = "",
    idempotency_key: str | None = None,
) -> tuple[EmailNotification, bool]:
    object_id_value = str(object_id or "")
    defaults = {
        "notification_type": notification_type,
        "recipient": str(recipient or "").strip(),
        "group_id": group_id,
        "object_type": object_type,
        "object_id": object_id_value,
    }
    if idempotency_key:
        return EmailNotification.objects.get_or_create(
            idempotency_key=idempotency_key,
            defaults=defaults,
        )
    notification = EmailNotification.objects.create(**defaults)
    return notification, True


def send_notification(
    notification: EmailNotification,
    *,
    subject: str,
    body_text: str,
    body_html: str = "",
) -> EmailNotification:
    if notification.status == EmailNotification.STATUS_SENT:
        return notification

    if not getattr(settings, "EMAIL_ENABLED", False):
        notification.status = EmailNotification.STATUS_SENT
        notification.sent_at = timezone.now()
        notification.provider_message_id = "email-disabled"
        notification.error_message = ""
        notification.save(
            update_fields=[
                "status",
                "sent_at",
                "provider_message_id",
                "error_message",
                "updated_at",
            ]
        )
        return notification

    try:
        connection = get_connection(fail_silently=False)
        from_email = getattr(
            settings, "EMAIL_FROM_DISPLAY", settings.DEFAULT_FROM_EMAIL
        )
        message = EmailMultiAlternatives(
            subject=subject,
            body=body_text,
            from_email=from_email,
            to=[notification.recipient],
            connection=connection,
        )
        if body_html:
            message.attach_alternative(body_html, "text/html")
        sent_count = message.send()
        if sent_count <= 0:
            raise RuntimeError("Le backend email n'a envoyé aucun message.")
    except Exception as exc:
        notification.status = EmailNotification.STATUS_FAILED
        notification.error_message = str(exc)[:2000]
        notification.save(update_fields=["status", "error_message", "updated_at"])
        logger.exception(
            "email_notification_failed type=%s notification_id=%s",
            notification.notification_type,
            notification.pk,
        )
        return notification

    notification.status = EmailNotification.STATUS_SENT
    notification.sent_at = timezone.now()
    notification.error_message = ""
    notification.save(
        update_fields=["status", "sent_at", "error_message", "updated_at"]
    )
    return notification


def send_transactional_email(
    *,
    notification_type: str,
    recipient: str,
    context: dict,
    group_id: int | None = None,
    object_type: str = "",
    object_id: str | int = "",
    idempotency_key: str | None = None,
) -> EmailNotification:
    notification, created = create_notification(
        notification_type=notification_type,
        recipient=recipient,
        group_id=group_id,
        object_type=object_type,
        object_id=object_id,
        idempotency_key=idempotency_key,
    )
    if not created and notification.status != EmailNotification.STATUS_PENDING:
        return notification

    template = render_email_template(notification_type, context)
    return send_notification(
        notification,
        subject=template.subject,
        body_text=template.body_text,
        body_html=template.body_html,
    )
