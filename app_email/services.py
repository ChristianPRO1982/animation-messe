import logging
from dataclasses import dataclass
from email.headerregistry import Address
from smtplib import SMTPAuthenticationError
from typing import Any

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.core.validators import validate_email
from django.db import IntegrityError, transaction
from django.template import Context, TemplateDoesNotExist
from django.template.loader import get_template
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from app_email.models import EmailNotification, EmailSettings

logger = logging.getLogger("app_email")


@dataclass(frozen=True)
class RenderedEmail:
    subject: str
    body_text: str
    body_html: str


def _normalize_subject(subject: str) -> str:
    normalized = " ".join(str(subject or "").split())
    raw_prefix = str(getattr(settings, "AM_EMAIL_SUBJECT_PREFIX", "") or "")
    prefix = " ".join(raw_prefix.split())
    if prefix and raw_prefix[-1].isspace():
        prefix += " "
    if prefix and not normalized.startswith(prefix):
        normalized = f"{prefix}{normalized}"
    return normalized


def get_sender_address(sender_key: str = "default") -> str:
    if sender_key == "planning":
        email = settings.AM_EMAIL_PLANNING_FROM_EMAIL
        name = settings.AM_EMAIL_PLANNING_FROM_NAME
    elif sender_key == "default":
        email = settings.DEFAULT_FROM_EMAIL
        name = settings.AM_EMAIL_FROM_NAME
    else:
        raise ValueError(_("Profil d'expediteur inconnu."))
    email = str(email or "").strip()
    name = str(name or "").strip()
    if name and email and "<" not in email and ">" not in email:
        return str(Address(display_name=name, addr_spec=email))
    return email


def get_email_settings() -> EmailSettings:
    return EmailSettings.objects.filter(pk=1).first() or EmailSettings(pk=1)


def set_email_enabled(enabled: bool) -> EmailSettings:
    with transaction.atomic():
        EmailSettings.objects.get_or_create(pk=1)
        configuration = EmailSettings.objects.select_for_update().get(pk=1)
        if configuration.enabled and not enabled:
            EmailNotification.objects.filter(
                status=EmailNotification.STATUS_BLOCKED_ADMIN
            ).update(
                status=EmailNotification.STATUS_BLOCKED_ADMIN_HISTORY,
                updated_at=timezone.now(),
            )
        configuration.enabled = enabled
        configuration.save(update_fields=["enabled"])
        return configuration


def _sanitize_error(error: object) -> str:
    # Backend messages may contain arbitrary credentials or message contents.
    if isinstance(error, SMTPAuthenticationError):
        return str(_("Authentification SMTP refusee."))
    if isinstance(error, TimeoutError):
        return str(_("Delai d'envoi email depasse."))
    if isinstance(error, TemplateDoesNotExist):
        return str(_("Template email introuvable."))
    return str(_("Echec technique de l'envoi email."))


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


def _render_text_template(template_name: str, context: dict[str, Any]) -> str:
    template = get_template(template_name)
    return template.template.render(Context(context, autoescape=False))


def render_email(notification_type: str, context: dict[str, Any]) -> RenderedEmail:
    template_root = f"emails/{notification_type}"
    subject = _normalize_subject(
        _render_text_template(f"{template_root}/subject.txt", context)
    )
    body_text = _render_text_template(f"{template_root}/body.txt", context)
    try:
        html_template = get_template(f"{template_root}/body.html")
    except TemplateDoesNotExist:
        body_html = ""
    else:
        body_html = html_template.render(context)
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
    sender_key: str = "default",
) -> EmailNotification:
    notification_type = str(notification_type or "").strip()
    recipient_email = str(recipient_email or "").strip()
    business_key = str(business_key or "").strip() or None
    if not notification_type:
        raise ValueError(_("Le type de notification est obligatoire."))
    validate_email(recipient_email)
    if sender_key not in {"default", "planning"}:
        raise ValueError(_("Profil d'expediteur inconnu."))
    content_object_type, content_object_id = _content_object_identity(content_object)
    defaults = {
        "sender_key": sender_key,
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
            notification = EmailNotification.objects.filter(
                business_key=business_key
            ).first()
            if notification is None:
                raise
            return notification

    return EmailNotification.objects.create(
        notification_type=notification_type,
        business_key=None,
        **defaults,
    )


def send_notification(
    notification: EmailNotification,
    context: dict[str, Any] | None = None,
) -> EmailNotification:
    if notification._state.adding or notification.pk is None:
        raise ValueError(_("La notification doit etre enregistree avant l'envoi."))

    database = notification._state.db or "default"
    notification.refresh_from_db(using=database)
    if notification.status != EmailNotification.STATUS_PENDING:
        return notification
    environment_enabled = getattr(settings, "AM_EMAIL_ENABLED", False)
    # Always acquire the global lock before notification locks, including in admin updates.
    with transaction.atomic(using=database):
        configuration = None
        if environment_enabled:
            configuration = (
                EmailSettings.objects.using(database)
                .select_for_update()
                .filter(pk=1)
                .first()
            )
        notification.refresh_from_db(
            using=database,
            from_queryset=EmailNotification.objects.using(database).select_for_update(),
        )
        if notification.status != EmailNotification.STATUS_PENDING:
            return notification
        if not environment_enabled:
            notification.mark_blocked(EmailNotification.STATUS_BLOCKED_ENV)
            return notification
        if configuration is None or not configuration.enabled:
            notification.mark_blocked(EmailNotification.STATUS_BLOCKED_ADMIN)
            return notification
        return _send_pending_notification(notification, context)


def _send_pending_notification(
    notification: EmailNotification,
    context: dict[str, Any] | None = None,
) -> EmailNotification:
    context = context or {}
    if notification.status != EmailNotification.STATUS_PENDING:
        return notification

    try:
        rendered = render_email(notification.notification_type, context)
        message = EmailMultiAlternatives(
            subject=rendered.subject,
            body=rendered.body_text,
            from_email=get_sender_address(notification.sender_key),
            to=[notification.recipient_email],
        )
        if rendered.body_html:
            message.attach_alternative(rendered.body_html, "text/html")
        sent_count = message.send(using="default")
        provider_message_id = getattr(message, "extra_headers", {}).get(
            "Message-ID", ""
        )
    except Exception as exc:
        error_message = _sanitize_error(exc)
    else:
        if sent_count:
            notification.mark_sent(provider_message_id=provider_message_id)
            return notification
        error_message = str(_("Le backend email n'a envoyé aucun message."))

    # Persist outside the exception handler to avoid chaining backend secrets.
    logger.error(
        "Email notification failed: %s",
        error_message,
        extra={
            "notification_id": notification.pk,
            "status": EmailNotification.STATUS_FAILED,
        },
    )
    notification.mark_failed(error_message)
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
    sender_key: str = "default",
) -> EmailNotification:
    notification = queue_email(
        notification_type,
        recipient_email,
        context,
        recipient_member_id=recipient_member_id,
        group=group,
        content_object=content_object,
        business_key=business_key,
        sender_key=sender_key,
    )
    return send_notification(notification, context)
