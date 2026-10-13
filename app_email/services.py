import logging
import re
from dataclasses import dataclass
from typing import Any

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.core.validators import validate_email
from django.db import IntegrityError, transaction
from django.template.loader import render_to_string
from django.template import TemplateDoesNotExist
from django.utils.translation import gettext_lazy as _

from app_email.models import EmailNotification

logger = logging.getLogger("app_email")
SENSITIVE_ERROR_RE = re.compile(
    r"(?i)\b(password|passwd|pwd|secret|token|api[_-]?key|authorization)=([^\s]+)"
)


@dataclass(frozen=True)
class RenderedEmail:
    subject: str
    body_text: str
    body_html: str


def _normalize_subject(subject: str) -> str:
    normalized = " ".join(str(subject or "").split())
    prefix = str(getattr(settings, "AM_EMAIL_SUBJECT_PREFIX", "") or "")
    if prefix and not normalized.startswith(prefix):
        normalized = f"{prefix}{normalized}"
    return normalized


def _from_email() -> str:
    email = str(getattr(settings, "DEFAULT_FROM_EMAIL", "") or "").strip()
    name = str(getattr(settings, "AM_EMAIL_FROM_NAME", "") or "").strip()
    if name and email and "<" not in email and ">" not in email:
        return f"{name} <{email}>"
    return email


def _sanitize_error(error: object) -> str:
    message = " ".join(str(error or "").split())
    message = SENSITIVE_ERROR_RE.sub(r"\1=***", message)
    return message[:1000]


def _content_object_identity(content_object: object | None) -> tuple[str, str]:
    if content_object is None:
        return "", ""
    meta = getattr(content_object, "_meta", None)
    object_type = (
        f"{meta.app_label}.{meta.model_name}"
        if meta is not None
        else content_object.__class__.__name__
    )
    object_id = str(getattr(content_object, "pk", "") or "")
    return object_type, object_id


def _group_id(group: object | None) -> int | None:
    if group is None:
        return None
    return getattr(group, "gg_id", group)


def render_email(notification_type: str, context: dict[str, Any]) -> RenderedEmail:
    template_root = f"emails/{notification_type}"
    subject = _normalize_subject(
        render_to_string(f"{template_root}/subject.txt", context)
    )
    body_text = render_to_string(f"{template_root}/body.txt", context)
    try:
        body_html = render_to_string(f"{template_root}/body.html", context)
    except TemplateDoesNotExist:
        body_html = ""
    return RenderedEmail(subject=subject, body_text=body_text, body_html=body_html)


def queue_email(
    notification_type: str,
    recipient_email: str,
    context: dict[str, Any] | None = None,
    *,
    recipient_member_id: str | None = None,
    group=None,
    content_object=None,
    business_key: str | None = None,
) -> EmailNotification:
    notification_type = str(notification_type or "").strip()
    recipient_email = str(recipient_email or "").strip()
    business_key = str(business_key or "").strip() or None
    if not notification_type:
        raise ValueError(_("Le type de notification est obligatoire."))
    validate_email(recipient_email)
    content_object_type, content_object_id = _content_object_identity(content_object)
    defaults = {
        "recipient_email": recipient_email,
        "recipient_member_id": recipient_member_id or None,
        "group_id": _group_id(group),
        "content_object_type": content_object_type,
        "content_object_id": content_object_id,
    }

    if business_key:
        try:
            with transaction.atomic():
                notification, _created = EmailNotification.objects.get_or_create(
                    business_key=business_key,
                    defaults={
                        "notification_type": notification_type,
                        **defaults,
                    },
                )
                return notification
        except IntegrityError:
            return EmailNotification.objects.get(business_key=business_key)

    return EmailNotification.objects.create(
        notification_type=notification_type,
        business_key=None,
        **defaults,
    )


def send_notification(
    notification: EmailNotification,
    context: dict[str, Any] | None = None,
) -> EmailNotification:
    context = context or {}
    if not getattr(settings, "AM_EMAIL_ENABLED", True):
        notification.mark_skipped(_("Envoi email désactivé."))
        return notification

    try:
        rendered = render_email(notification.notification_type, context)
        message = EmailMultiAlternatives(
            subject=rendered.subject,
            body=rendered.body_text,
            from_email=_from_email(),
            to=[notification.recipient_email],
        )
        if rendered.body_html:
            message.attach_alternative(rendered.body_html, "text/html")
        sent_count = message.send(using="default")
        provider_message_id = getattr(message, "extra_headers", {}).get(
            "Message-ID", ""
        )
        if sent_count:
            notification.mark_sent(provider_message_id=provider_message_id)
        else:
            notification.mark_failed(_("Le backend email n'a envoyé aucun message."))
    except Exception as exc:
        error_message = _sanitize_error(exc)
        notification.mark_failed(error_message)
        logger.exception(
            "Email notification failed",
            extra={
                "notification_id": notification.pk,
                "notification_type": notification.notification_type,
                "status": notification.status,
            },
        )
    return notification


def send_email_now(
    notification_type: str,
    recipient_email: str,
    context: dict[str, Any] | None = None,
    *,
    recipient_member_id: str | None = None,
    group=None,
    content_object=None,
    business_key: str | None = None,
) -> EmailNotification:
    notification = queue_email(
        notification_type,
        recipient_email,
        context,
        recipient_member_id=recipient_member_id,
        group=group,
        content_object=content_object,
        business_key=business_key,
    )
    return send_notification(notification, context)

