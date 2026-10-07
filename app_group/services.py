from __future__ import annotations

from collections.abc import Iterable
from datetime import timedelta

from django.contrib.auth.hashers import check_password, make_password
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.validators import validate_email
from django.db import transaction
from django.utils import timezone
from django.utils.crypto import salted_hmac
from django.utils.translation import gettext_lazy as _

from app_group.models import (
    MEMBER_KIND_ACCOUNT,
    MEMBER_KIND_AM,
    REQUEST_TYPE_AM_ACCESS,
    ROLE_RESPONSABLE_IMPRESSION,
    AccessRequest,
    AmMember,
    AmMemberRequest,
    AmMemberTitle,
    CelebrationRule,
    CommonGroup,
    CommonGroupTag,
    CommonGroupUser,
    Group,
    GroupFunction,
    GroupLocation,
    GroupMember,
    GroupMemberFunction,
    GroupMemberRole,
    GroupRole,
    PlanningState,
    Song,
    SongTag,
    SongTagVerse,
    SpecialDateCelebration,
    SpecialDateRule,
    Verse,
)
from app_member.models import Member

AM_MEMBER_REQUEST_TTL_DAYS = 14
REFUSED_REQUEST_PURGE_DAYS = 14


def hash_personal_secret(raw_secret: str) -> str:
    raw_secret = str(raw_secret or "").strip()
    if not raw_secret:
        raise ValidationError(_("Le secret personnel est obligatoire."))
    return make_password(raw_secret)


def check_personal_secret(raw_secret: str, encoded_secret: str) -> bool:
    return check_password(str(raw_secret or ""), encoded_secret)


def email_fingerprint(email: str) -> str:
    normalized_email = str(email or "").strip().lower()
    if not normalized_email:
        raise ValidationError(_("L'adresse email est obligatoire."))
    return salted_hmac("app_group.am_member_email", normalized_email).hexdigest()


def _user_member_id(user) -> str:
    member_id = str(getattr(user, "external_id", "") or "").strip()
    if not member_id:
        raise PermissionDenied(_("Utilisateur sans identifiant membre."))
    return member_id


def is_common_group_responsable(group_id: int, member_id: str) -> bool:
    return CommonGroupUser.objects.filter(
        group_id=group_id,
        member_id=member_id,
        is_group_admin=True,
    ).exists()


def can_manage_group(user, group: Group) -> bool:
    if not getattr(user, "is_authenticated", False):
        return False
    if getattr(user, "is_admin", False):
        return True
    return is_common_group_responsable(group.gg_id, _user_member_id(user))


def require_group_manager(user, group: Group) -> None:
    if not can_manage_group(user, group):
        raise PermissionDenied(_("Accès refusé au groupe."))


def ensure_group_environment(
    common_group_id: int,
    *,
    celebration_retention_months: int = 24,
) -> Group:
    if not CommonGroup.objects.filter(group_id=common_group_id).exists():
        raise ValidationError(_("Le groupe commun est introuvable."))

    group, _created = Group.objects.get_or_create(
        gg_id=common_group_id,
        defaults={"celebration_retention_months": celebration_retention_months},
    )
    return group


def ensure_responsable_impression_role(group: Group) -> GroupRole:
    role, _created = GroupRole.objects.get_or_create(
        group=group,
        code=ROLE_RESPONSABLE_IMPRESSION,
        defaults={
            "label": _("Responsable impression"),
            "is_system": True,
            "is_active": True,
        },
    )
    update_fields = []
    if not role.is_system:
        role.is_system = True
        update_fields.append("is_system")
    if not role.is_active:
        role.is_active = True
        update_fields.append("is_active")
    if str(role.label) != str(_("Responsable impression")):
        role.label = _("Responsable impression")
        update_fields.append("label")
    if update_fields:
        role.save(update_fields=update_fields)
    return role


def _ensure_account_group_member(group_member: GroupMember) -> None:
    if (
        group_member.member_kind != MEMBER_KIND_ACCOUNT
        or group_member.member_id is None
    ):
        raise ValidationError(_("Seul un membre avec compte peut recevoir ce droit."))


def _ensure_same_group(left_group_id: int, right_group_id: int) -> None:
    if left_group_id != right_group_id:
        raise ValidationError(_("Les objets doivent appartenir au même groupe."))


def assign_responsable_impression(group_member: GroupMember) -> GroupMemberRole:
    _ensure_account_group_member(group_member)
    role = ensure_responsable_impression_role(group_member.group)
    assignment, _created = GroupMemberRole.objects.get_or_create(
        group_member=group_member,
        role=role,
    )
    return assignment


def remove_responsable_impression(group_member: GroupMember) -> int:
    role = ensure_responsable_impression_role(group_member.group)
    deleted_count, _details = GroupMemberRole.objects.filter(
        group_member=group_member,
        role=role,
    ).delete()
    return deleted_count


def set_common_responsable(group_id: int, member_id: str, *, enabled: bool) -> None:
    with transaction.atomic():
        memberships = CommonGroupUser.objects.select_for_update().filter(
            group_id=group_id
        )
        if not enabled:
            responsable_count = memberships.filter(is_group_admin=True).count()
            is_target_responsable = memberships.filter(
                member_id=member_id,
                is_group_admin=True,
            ).exists()
            if is_target_responsable and responsable_count <= 1:
                raise ValidationError(
                    _("Un groupe doit conserver au moins un Responsable.")
                )

        updated = memberships.filter(member_id=member_id).update(is_group_admin=enabled)
        if not updated:
            raise ValidationError(_("L'appartenance commune est introuvable."))


def assign_group_function(
    group_member: GroupMember,
    function: GroupFunction,
) -> GroupMemberFunction:
    _ensure_same_group(group_member.group_id, function.group_id)
    assignment, _created = GroupMemberFunction.objects.get_or_create(
        group_member=group_member,
        function=function,
    )
    return assignment


def remove_group_function(
    group_member: GroupMember,
    function: GroupFunction,
) -> int:
    _ensure_same_group(group_member.group_id, function.group_id)
    deleted_count, _details = GroupMemberFunction.objects.filter(
        group_member=group_member,
        function=function,
    ).delete()
    return deleted_count


def save_group_function(function: GroupFunction) -> GroupFunction:
    function.full_clean()
    function.save()
    return function


def save_group_settings(group: Group) -> Group:
    group.full_clean()
    group.save(update_fields=["celebration_retention_months", "updated_at"])
    return group


def save_am_member_title(title: AmMemberTitle) -> AmMemberTitle:
    title.full_clean()
    title.save()
    return title


def save_group_location(location: GroupLocation) -> GroupLocation:
    location.full_clean()
    location.save()
    return location


def save_planning_state(state: PlanningState) -> PlanningState:
    state.full_clean()
    state.save()
    return state


def create_access_request(
    group: Group,
    member: Member,
    *,
    consent_version: str,
    consented_at=None,
) -> AccessRequest:
    membership = CommonGroupUser.objects.filter(
        group_id=group.gg_id,
        member_id=member.mm_id,
    ).first()
    if membership is None:
        raise ValidationError(_("Le membre n'appartient pas au groupe commun."))
    if membership.am_access:
        raise ValidationError(_("Le membre possède déjà l'accès AM."))

    request, _created = AccessRequest.objects.get_or_create(
        group=group,
        member=member,
        request_type=REQUEST_TYPE_AM_ACCESS,
        defaults={
            "consent_version": consent_version,
            "consented_at": consented_at,
        },
    )
    return request


def accept_access_request(access_request: AccessRequest) -> GroupMember:
    with transaction.atomic():
        membership = (
            CommonGroupUser.objects.select_for_update()
            .filter(
                group_id=access_request.group_id,
                member_id=access_request.member_id,
            )
            .first()
        )
        if membership is None:
            raise ValidationError(_("L'appartenance commune est introuvable."))

        membership.am_access = True
        membership.save(update_fields=["am_access"])
        group_member, _created = GroupMember.objects.get_or_create(
            group=access_request.group,
            member=access_request.member,
            member_kind=MEMBER_KIND_ACCOUNT,
        )
        access_request.delete()
        return group_member


def refuse_access_request(access_request: AccessRequest) -> None:
    access_request.delete()


def create_am_member_request(
    group: Group,
    requested_by: GroupMember,
    *,
    first_name: str,
    last_name: str,
    email: str,
    consent_token: str,
    consent_version: str,
    expires_at=None,
    now=None,
) -> AmMemberRequest:
    _ensure_same_group(requested_by.group_id, group.gg_id)
    _ensure_account_group_member(requested_by)
    if not is_common_group_responsable(group.gg_id, requested_by.member_id):
        raise PermissionDenied(_("Seul un Responsable peut inviter un Membre AM."))

    first_name = str(first_name or "").strip()
    last_name = str(last_name or "").strip()
    email = str(email or "").strip()
    consent_version = str(consent_version or "").strip()
    if not first_name or not last_name:
        raise ValidationError(_("Le nom et le prénom du Membre AM sont obligatoires."))
    validate_email(email)
    if not consent_version:
        raise ValidationError(_("La version du consentement est obligatoire."))

    now = now or timezone.now()
    max_expires_at = now + timedelta(days=AM_MEMBER_REQUEST_TTL_DAYS)
    expires_at = expires_at or max_expires_at
    if expires_at <= now or expires_at > max_expires_at:
        raise ValidationError(_("La demande de Membre AM doit expirer sous 14 jours."))

    request = AmMemberRequest.objects.create(
        group=group,
        requested_by=requested_by,
        first_name=first_name,
        last_name=last_name,
        email=email,
        consent_token_hash=hash_personal_secret(consent_token),
        consent_version=consent_version,
        expires_at=expires_at,
    )
    return request


def _display_hint(first_name: str, last_name: str) -> str:
    label = " ".join(part for part in (first_name, last_name) if part).strip()
    return label[:1] + "***" if label else ""


def expire_am_member_request(request: AmMemberRequest, *, now=None) -> bool:
    now = now or timezone.now()
    if request.status != AmMemberRequest.STATUS_PENDING or request.expires_at > now:
        return False

    request.status = AmMemberRequest.STATUS_EXPIRED
    request.display_hint = _display_hint(request.first_name, request.last_name)
    request.first_name = ""
    request.last_name = ""
    request.email = ""
    request.consent_token_hash = hash_personal_secret("expired")
    request.purge_at = now
    request.save(
        update_fields=[
            "status",
            "display_hint",
            "first_name",
            "last_name",
            "email",
            "consent_token_hash",
            "purge_at",
            "updated_at",
        ]
    )
    return True


def refuse_am_member_request(request: AmMemberRequest, *, now=None) -> None:
    now = now or timezone.now()
    request.status = AmMemberRequest.STATUS_REFUSED
    request.refused_at = now
    request.display_hint = _display_hint(request.first_name, request.last_name)
    request.first_name = ""
    request.last_name = ""
    request.email = ""
    request.consent_token_hash = hash_personal_secret("refused")
    request.purge_at = now + timedelta(days=REFUSED_REQUEST_PURGE_DAYS)
    request.save(
        update_fields=[
            "status",
            "refused_at",
            "display_hint",
            "first_name",
            "last_name",
            "email",
            "consent_token_hash",
            "purge_at",
            "updated_at",
        ]
    )


def accept_am_member_request(
    request: AmMemberRequest,
    *,
    consent_token: str,
    withdrawal_secret: str,
    functions: Iterable[GroupFunction] = (),
    title=None,
    now=None,
) -> AmMember:
    now = now or timezone.now()
    if request.status != AmMemberRequest.STATUS_PENDING:
        raise ValidationError(_("La demande n'est plus en attente."))
    if request.expires_at <= now:
        expire_am_member_request(request, now=now)
        raise ValidationError(_("La demande de Membre AM a expiré."))
    if not check_personal_secret(consent_token, request.consent_token_hash):
        raise ValidationError(_("Le jeton de consentement est invalide."))
    if title is not None:
        _ensure_same_group(request.group_id, title.group_id)

    with transaction.atomic():
        group_member = GroupMember.objects.create(
            group=request.group,
            member=None,
            member_kind=MEMBER_KIND_AM,
            joined_at=now,
        )
        am_member = AmMember.objects.create(
            group_member=group_member,
            first_name=request.first_name.strip(),
            last_name=request.last_name.strip(),
            title=title,
            consented_at=now,
            consent_version=request.consent_version,
            consent_email_fingerprint=email_fingerprint(request.email),
            withdrawal_secret_hash=hash_personal_secret(withdrawal_secret),
        )
        for function in functions:
            assign_group_function(group_member, function)
        request.delete()
        return am_member


def add_song_to_repertoire(
    group: Group,
    *,
    song_id: int,
    verse_ids: Iterable[int] = (),
) -> Song:
    song, _created = Song.objects.get_or_create(group=group, song_id=song_id)
    for verse_id in verse_ids:
        Verse.objects.get_or_create(song=song, verse_id=verse_id)
    return song


def tag_song(song: Song, group_tag: CommonGroupTag) -> SongTag:
    _ensure_same_group(song.group_id, group_tag.group_id)
    song_tag, _created = SongTag.objects.get_or_create(song=song, group_tag=group_tag)
    for verse in Verse.objects.filter(song=song):
        SongTagVerse.objects.get_or_create(song_tag=song_tag, verse=verse)
    return song_tag


def set_tag_verse_selection(
    song_tag: SongTag,
    verse: Verse,
    *,
    selected_by_default: bool,
) -> SongTagVerse:
    _ensure_same_group(song_tag.song_id, verse.song_id)
    selection, _created = SongTagVerse.objects.update_or_create(
        song_tag=song_tag,
        verse=verse,
        defaults={"selected_by_default": selected_by_default},
    )
    return selection


def validate_celebration_rule_parent_group(rule) -> None:
    parent = getattr(rule, "parent", None)
    if parent is not None:
        _ensure_same_group(rule.group_id, parent.group_id)


def save_celebration_rule(rule: CelebrationRule) -> CelebrationRule:
    _ensure_same_group(rule.group_id, rule.location.group_id)
    validate_celebration_rule_parent_group(rule)
    rule.full_clean()
    rule.save()
    return rule


def create_celebration_rule(
    group: Group,
    *,
    weekday: int,
    time,
    location,
    parent: CelebrationRule | None = None,
    position: int = 0,
    is_active: bool = True,
) -> CelebrationRule:
    rule = CelebrationRule(
        group=group,
        weekday=weekday,
        time=time,
        location=location,
        parent=parent,
        position=position,
        is_active=is_active,
    )
    return save_celebration_rule(rule)


def validate_special_date_rule_fields(rule: SpecialDateRule) -> None:
    if rule.rule_type == SpecialDateRule.RULE_ANNUAL_FIXED:
        if rule.month is None or rule.day is None:
            raise ValidationError(_("Une date annuelle fixe requiert mois et jour."))
    elif rule.rule_type == SpecialDateRule.RULE_ONE_OFF:
        if rule.exact_date is None:
            raise ValidationError(_("Une date ponctuelle requiert une date exacte."))
    elif rule.rule_type == SpecialDateRule.RULE_NTH_WEEKDAY:
        if rule.month is None or rule.weekday is None or rule.occurrence is None:
            raise ValidationError(
                _("Une date récurrente requiert mois, jour de semaine et occurrence.")
            )
    else:
        raise ValidationError(_("Type de règle spéciale non pris en charge."))


def save_special_date_rule(rule: SpecialDateRule) -> SpecialDateRule:
    validate_special_date_rule_fields(rule)
    rule.full_clean()
    rule.save()
    return rule


def create_special_date_rule(
    group: Group,
    *,
    name: str,
    rule_type: str,
    collision_mode: str,
    month: int | None = None,
    day: int | None = None,
    exact_date=None,
    weekday: int | None = None,
    occurrence: int | None = None,
    is_active: bool = True,
) -> SpecialDateRule:
    rule = SpecialDateRule(
        group=group,
        name=name,
        rule_type=rule_type,
        collision_mode=collision_mode,
        month=month,
        day=day,
        exact_date=exact_date,
        weekday=weekday,
        occurrence=occurrence,
        is_active=is_active,
    )
    return save_special_date_rule(rule)


def validate_special_date_celebration_parent_rule(
    celebration: SpecialDateCelebration,
) -> None:
    parent = getattr(celebration, "parent", None)
    if parent is not None:
        celebration_rule_id = celebration.special_date_rule_id
        parent_rule_id = parent.special_date_rule_id
        if celebration_rule_id is not None and parent_rule_id is not None:
            if celebration_rule_id != parent_rule_id:
                raise ValidationError(
                    _("La célébration liée doit appartenir à la même règle spéciale.")
                )
        elif celebration.special_date_rule is not parent.special_date_rule:
            raise ValidationError(
                _("La célébration liée doit appartenir à la même règle spéciale.")
            )


def save_special_date_celebration(
    celebration: SpecialDateCelebration,
) -> SpecialDateCelebration:
    _ensure_same_group(
        celebration.special_date_rule.group_id, celebration.location.group_id
    )
    validate_special_date_celebration_parent_rule(celebration)
    celebration.full_clean()
    celebration.save()
    return celebration


def create_special_date_celebration(
    special_date_rule: SpecialDateRule,
    *,
    time,
    location,
    parent: SpecialDateCelebration | None = None,
    position: int = 0,
) -> SpecialDateCelebration:
    celebration = SpecialDateCelebration(
        special_date_rule=special_date_rule,
        time=time,
        location=location,
        parent=parent,
        position=position,
    )
    return save_special_date_celebration(celebration)
