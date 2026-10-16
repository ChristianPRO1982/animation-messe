import logging
import secrets
from datetime import timedelta
from urllib.parse import urlsplit

from django.conf import settings
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.decorators.debug import sensitive_variables

from app_email.models import EmailNotification
from app_email.services import send_private_email_now
from app_group import services
from app_group.models import (
    MEMBER_KIND_AM,
    AmMember,
    AmMemberRequest,
    CommonGroup,
    CommonGroupUser,
    GroupMember,
    GroupMemberFunction,
)

logger = logging.getLogger("app_email")
INVITATION_TYPE = "group_am_member_invitation"


def public_origin():
    origin = settings.AM_PUBLIC_ORIGIN.rstrip("/")
    parsed = urlsplit(origin)
    local = parsed.hostname in {"localhost", "127.0.0.1", "::1"}
    if (
        not parsed.netloc
        or parsed.username
        or parsed.password
        or parsed.path
        or parsed.query
        or parsed.fragment
        or (parsed.scheme != "https" and not (local and parsed.scheme == "http"))
    ):
        raise ValidationError(_("L'origine publique des invitations est invalide."))
    return origin


def invitation_key(invitation):
    return f"group_am_member_invitation:{invitation.public_id}"


@sensitive_variables()
def invite_am_member(group, requested_by, *, first_name, last_name, email, on_result):
    origin = public_origin()
    consent = services.get_current_group_consent(group)
    consent_token = secrets.token_urlsafe(32)
    withdrawal_secret = secrets.token_urlsafe(32)
    with transaction.atomic():
        invitation = services.create_am_member_request(
            group,
            requested_by,
            first_name=first_name,
            last_name=last_name,
            email=email,
            consent_token=consent_token,
            consent_version=consent.version_label,
            consent_message=consent.message,
            consent_body_markdown=consent.body_markdown,
            withdrawal_secret=withdrawal_secret,
        )
        invitation.purge_at = invitation.created_at + timedelta(days=7)
        invitation.save(update_fields=["purge_at"])
        notification = EmailNotification.objects.create(
            notification_type=INVITATION_TYPE,
            recipient_email="",
            group=group,
            business_key=invitation_key(invitation),
            content_object_type="app_group.ammemberrequest",
            content_object_id=str(invitation.pk),
        )
        group_name = CommonGroup.objects.get(pk=group.pk).name
        context = {
            "first_name": first_name,
            "last_name": last_name,
            "group_name": group_name,
            "consent_version": consent.version_label,
            "consent_body": consent.body_markdown,
            "expires_at": invitation.expires_at,
            "consent_url": origin
            + reverse("am_member_consent", args=[invitation.public_id])
            + "#"
            + consent_token,
            "withdrawal_url": origin
            + reverse("am_member_withdraw", args=[invitation.public_id])
            + "#"
            + withdrawal_secret,
        }

        @sensitive_variables()
        def deliver():
            try:
                result = send_private_email_now(
                    INVITATION_TYPE,
                    email,
                    context,
                    business_key=notification.business_key,
                    group=group,
                    content_object=invitation,
                )
                if result.status == EmailNotification.STATUS_SENT:
                    AmMemberRequest.objects.filter(pk=invitation.pk).update(
                        purge_at=None
                    )
            except Exception:
                # Never let callback exception details expose the transient recipient.
                logger.error("Echec technique de l'invitation Membre AM.")
                on_result(None)
            else:
                on_result(result)

        transaction.on_commit(deliver, robust=True)
    return invitation


def locked_invitation(public_id, secret, *, withdrawal=False):
    invitation = (
        AmMemberRequest.objects.select_for_update().filter(public_id=public_id).first()
    )
    if invitation is None:
        raise ValidationError(_("Ce lien est invalide ou n'est plus disponible."))
    now = timezone.now()
    if (
        invitation.status != AmMemberRequest.STATUS_PENDING
        or invitation.expires_at <= now
        or (invitation.purge_at is not None and invitation.purge_at <= now)
        or not services.check_personal_secret(
            secret,
            invitation.withdrawal_secret_hash
            if withdrawal
            else invitation.consent_token_hash,
        )
    ):
        raise ValidationError(_("Ce lien est invalide ou n'est plus disponible."))
    return invitation


@transaction.atomic
@sensitive_variables()
def consent_decision(public_id, secret, *, action):
    invitation = locked_invitation(public_id, secret)
    if action == "accept":
        if not invitation.withdrawal_secret_hash:
            raise ValidationError(_("Cette invitation doit être recréée."))
        return services.accept_am_member_request(invitation, consent_token=secret)
    if action == "refuse":
        invitation.delete()
        return None
    raise ValidationError(_("Action invalide."))


@transaction.atomic
@sensitive_variables()
def withdraw(public_id, secret, *, confirm=False):
    # Lock the request first, as acceptance does, then inspect the active profile.
    invitation = (
        AmMemberRequest.objects.select_for_update().filter(public_id=public_id).first()
    )
    if invitation is not None:
        invitation = locked_invitation(public_id, secret, withdrawal=True)
        if confirm:
            invitation.delete()
            return None
        return {
            "first_name": invitation.first_name,
            "last_name": invitation.last_name,
            "group_id": invitation.group_id,
        }
    profile = AmMember.objects.select_for_update().filter(public_id=public_id).first()
    if profile is None or not services.check_personal_secret(
        secret, profile.withdrawal_secret_hash
    ):
        raise ValidationError(_("Ce lien est invalide ou n'est plus disponible."))
    if confirm:
        GroupMember.objects.get(
            pk=profile.group_member_id, member_kind=MEMBER_KIND_AM
        ).delete()
        return None
    return {
        "first_name": profile.first_name,
        "last_name": profile.last_name,
        "group_id": profile.group_member.group_id,
    }


def require_am_access(user, group):
    if not getattr(user, "is_authenticated", False):
        raise PermissionDenied
    if getattr(user, "is_admin", False):
        return
    if not CommonGroupUser.objects.filter(
        group_id=group.pk, member_id=getattr(user, "external_id", None), am_access=True
    ).exists():
        raise PermissionDenied


@transaction.atomic
def update_am_member(user, group, member_id, *, title_id=None, function_ids=()):
    require_am_access(user, group)
    profile = (
        AmMember.objects.select_for_update()
        .filter(group_member_id=member_id, group_member__group=group)
        .first()
    )
    if profile is None:
        raise ValidationError(_("Membre AM introuvable dans ce groupe."))
    title = (
        group.am_member_titles.filter(pk=title_id, is_active=True).first()
        if title_id
        else None
    )
    if title_id and title is None:
        raise ValidationError(_("Titre invalide pour ce groupe."))
    functions = list(group.functions.filter(pk__in=function_ids, is_active=True))
    if len(functions) != len(set(function_ids)):
        raise ValidationError(_("Fonctions invalides pour ce groupe."))
    profile.title = title
    profile.save(update_fields=["title", "updated_at"])
    GroupMemberFunction.objects.filter(group_member_id=member_id).exclude(
        function_id__in=function_ids
    ).delete()
    for function in functions:
        services.assign_group_function(profile.group_member, function)


@transaction.atomic
def delete_am_member(user, group, member_id):
    services.require_group_manager(user, group)
    profile = (
        AmMember.objects.select_for_update()
        .filter(
            group_member_id=member_id,
            group_member__group=group,
            group_member__member_kind=MEMBER_KIND_AM,
        )
        .first()
    )
    if profile is None:
        raise ValidationError(_("Membre AM introuvable dans ce groupe."))
    GroupMember.objects.get(pk=member_id).delete()
