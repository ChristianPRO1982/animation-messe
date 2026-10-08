from __future__ import annotations

import json
import secrets
from types import SimpleNamespace

from django.contrib import messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import Http404, HttpResponseForbidden
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from app_group import forms, services
from app_group.models import (
    MEMBER_KIND_ACCOUNT,
    REQUEST_TYPE_AM_ACCESS,
    ROLE_RESPONSABLE_IMPRESSION,
    AccessRequest,
    AmMemberRequest,
    AmMemberTitle,
    CommonGroup,
    CommonGroupJoinRequest,
    CommonGroupTag,
    CommonGroupUser,
    Group,
    GroupFunction,
    GroupLocation,
    GroupMember,
    PlanningState,
    SongTag,
    Verse,
)
from app_main.models import DirectoryUserRecord
from app_member.models import Member

INVITATION_NOTICE_SESSION_KEY = "app_group_invitation_notice"

GROUP_PAGE_CONFIG = {
    "members": {
        "template": "app_group/group_members.html",
        "title": _("Membres"),
        "route": "group_members",
        "actions": {
            "assign_responsable_impression",
            "remove_responsable_impression",
            "accept_access_request",
            "refuse_access_request",
            "accept_common_join_request",
            "refuse_common_join_request",
            "remove_member_am_access",
            "remove_common_group_member",
        },
    },
    "responsables": {
        "template": "app_group/group_responsables.html",
        "title": _("Responsables"),
        "route": "group_responsables",
        "actions": {"set_common_responsable"},
    },
    "am_members": {
        "template": "app_group/group_am_members.html",
        "title": _("Membres AM"),
        "route": "group_am_members",
        "actions": {
            "create_am_member_request",
            "accept_am_member_request",
            "refuse_am_member_request",
            "expire_am_member_request",
        },
    },
    "functions": {
        "template": "app_group/group_functions.html",
        "title": _("Fonctions"),
        "route": "group_functions",
        "actions": {"save_function", "assign_function", "remove_function"},
    },
    "am_member_titles": {
        "template": "app_group/group_am_member_titles.html",
        "title": _("Titres Membre AM"),
        "route": "group_am_member_titles",
        "actions": {"save_am_member_title"},
    },
    "calendar_states": {
        "template": "app_group/group_calendar_states.html",
        "title": _("États planning"),
        "route": "group_calendar_states",
        "actions": {"save_planning_state"},
    },
    "calendar_regular_rules": {
        "template": "app_group/group_calendar_regular_rules.html",
        "title": _("Règles régulières"),
        "route": "group_calendar_regular_rules",
        "actions": {"create_celebration_rule"},
    },
    "calendar_special_dates": {
        "template": "app_group/group_calendar_special_dates.html",
        "title": _("Dates particulières"),
        "route": "group_calendar_special_dates",
        "actions": {"create_special_date_rule"},
    },
    "settings": {
        "template": "app_group/group_settings.html",
        "title": _("Paramètres généraux"),
        "route": "group_settings",
        "actions": {"save_group_settings"},
    },
    "locations": {
        "template": "app_group/group_locations.html",
        "title": _("Lieux"),
        "route": "group_locations",
        "actions": {"save_location"},
    },
    "songs": {
        "template": "app_group/group_songs.html",
        "title": _("Recueil"),
        "route": "group_songs",
        "actions": {"add_song", "tag_song", "set_tag_verse_selection"},
    },
}


def groups_home(request):
    if request.method == "POST":
        return _handle_groups_home_post(request)

    return render(
        request,
        "app_group/groups_home.html",
        _build_groups_home_context(request),
    )


def _handle_groups_home_post(request):
    if not request.user.is_authenticated:
        return redirect("login")

    action = request.POST.get("action", "").strip()
    if action == "request_common_group_join":
        form = forms.JoinGroupRequestForm(request.POST)
        if not form.is_valid():
            messages.error(request, _("Demande de rattachement invalide."))
            return redirect("groups_home")

        try:
            services.create_common_join_request(
                form.cleaned_data["common_group_id"],
                str(getattr(request.user, "external_id", "") or "").strip(),
            )
        except (PermissionDenied, ValidationError, ValueError) as exc:
            messages.error(request, _validation_message(exc))
        else:
            messages.success(request, _("Votre demande de rattachement est envoyée."))
        return redirect("groups_home")

    if action == "request_am_access":
        form = forms.PublicAccessRequestForm(request.POST)
        if not form.is_valid():
            messages.error(request, _("Demande d'accès AM invalide."))
            return redirect("groups_home")

        common_group_id = form.cleaned_data["common_group_id"]
        member = Member(mm_id=str(getattr(request.user, "external_id", "") or ""))
        group = Group.objects.filter(gg_id=common_group_id).first()
        if group is None:
            messages.error(request, _("L'espace AM du groupe est introuvable."))
            return redirect("groups_home")

        try:
            services.create_access_request(
                group,
                member,
                consent_version="v1",
                consented_at=timezone.now(),
            )
        except (PermissionDenied, ValidationError, ValueError) as exc:
            messages.error(request, _validation_message(exc))
        else:
            messages.success(request, _("Votre demande d'accès AM est envoyée."))
        return redirect("groups_home")

    messages.error(request, _("Demande groupe invalide."))
    return redirect("groups_home")


def _build_groups_home_context(request):
    active_group_ids = list(Group.objects.values_list("gg_id", flat=True))
    common_groups = list(
        CommonGroup.objects.filter(group_id__in=active_group_ids).order_by("name")
    )
    member_group_ids: set[int] = set()
    am_access_group_ids: set[int] = set()
    responsable_group_ids: set[int] = set()
    pending_group_ids: set[int] = set()
    pending_am_access_group_ids: set[int] = set()
    is_authenticated = getattr(request.user, "is_authenticated", False)
    is_global_admin = bool(getattr(request.user, "is_admin", False))
    if is_authenticated:
        member_id = str(getattr(request.user, "external_id", "") or "").strip()
        if member_id:
            memberships = list(CommonGroupUser.objects.filter(member_id=member_id))
            member_group_ids = {membership.group_id for membership in memberships}
            am_access_group_ids = {
                membership.group_id
                for membership in memberships
                if membership.am_access
            }
            responsable_group_ids = {
                membership.group_id
                for membership in memberships
                if membership.is_group_admin
            }
            pending_group_ids = set(
                CommonGroupJoinRequest.objects.filter(member_id=member_id).values_list(
                    "group_id", flat=True
                )
            )
            pending_am_access_group_ids = set(
                AccessRequest.objects.filter(
                    member_id=member_id,
                    request_type=REQUEST_TYPE_AM_ACCESS,
                ).values_list("group_id", flat=True)
            )

    def sort_key(common_group):
        if common_group.group_id in member_group_ids:
            priority = 0
        elif common_group.status == CommonGroup.STATUS_OPEN:
            priority = 1
        else:
            priority = 2
        return priority, common_group.name.lower(), common_group.group_id

    rows = []
    for common_group in sorted(common_groups, key=sort_key):
        is_member = common_group.group_id in member_group_ids
        has_am_access = common_group.group_id in am_access_group_ids
        is_responsable = common_group.group_id in responsable_group_ids
        has_pending_request = common_group.group_id in pending_group_ids
        has_pending_am_access_request = (
            common_group.group_id in pending_am_access_group_ids
        )
        rows.append(
            {
                "common_group": common_group,
                "is_member": is_member,
                "has_am_access": has_am_access,
                "is_responsable": is_responsable,
                "can_enter_group": has_am_access or is_responsable or is_global_admin,
                "has_pending_request": has_pending_request,
                "has_pending_am_access_request": has_pending_am_access_request,
                "can_request_join": (
                    is_authenticated and not is_member and not has_pending_request
                ),
                "can_request_am_access": (
                    is_authenticated
                    and is_member
                    and not has_am_access
                    and not is_responsable
                    and not has_pending_am_access_request
                ),
            }
        )

    return {
        "rows": rows,
        "selected_group": None,
        "is_authenticated": is_authenticated,
    }


def groups_manage(request):
    if not request.user.is_authenticated:
        return redirect("login")

    if request.method == "POST":
        return _handle_manage_post(request)

    common_groups = _manageable_common_groups(request.user)
    am_group_ids = set(
        Group.objects.filter(
            gg_id__in=[group.group_id for group in common_groups]
        ).values_list("gg_id", flat=True)
    )
    rows = [
        {
            "common_group": common_group,
            "is_am_enabled": common_group.group_id in am_group_ids,
        }
        for common_group in common_groups
    ]
    return render(
        request,
        "app_group/groups_manage.html",
        {
            "rows": rows,
            "selected_group": None,
        },
    )


def group_detail(request, group_id: int):
    if not request.user.is_authenticated:
        return redirect("login")

    common_group = _get_common_group(group_id)
    group = Group.objects.filter(gg_id=group_id).first()
    access_context = _build_group_access_context(request.user, common_group, group)
    if not access_context.can_enter_group:
        return HttpResponseForbidden(_("Accès refusé."))

    if request.method == "POST":
        return _handle_group_post(
            request,
            common_group,
            group,
            redirect_name="group_detail",
            allowed_actions={"activate_group"},
        )

    context = _build_group_context(
        request,
        common_group,
        group,
        access_context=access_context,
    )
    return render(request, "app_group/group_detail.html", context)


def group_members(request, group_id: int):
    return _group_management_page(request, group_id, "members")


def group_responsables(request, group_id: int):
    return _group_management_page(request, group_id, "responsables")


def group_am_members(request, group_id: int):
    return _group_management_page(request, group_id, "am_members")


def group_functions(request, group_id: int):
    return _group_management_page(request, group_id, "functions")


def group_am_member_titles(request, group_id: int):
    return _group_management_page(request, group_id, "am_member_titles")


def group_calendar_states(request, group_id: int):
    return _group_management_page(request, group_id, "calendar_states")


def group_calendar_regular_rules(request, group_id: int):
    return _group_management_page(request, group_id, "calendar_regular_rules")


def group_calendar_special_dates(request, group_id: int):
    return _group_management_page(request, group_id, "calendar_special_dates")


def group_settings(request, group_id: int):
    return _group_management_page(request, group_id, "settings")


def group_locations(request, group_id: int):
    return _group_management_page(request, group_id, "locations")


def group_songs(request, group_id: int):
    return _group_management_page(request, group_id, "songs")


def _handle_manage_post(request):
    form = forms.ActivateGroupForm(request.POST)
    if form.is_valid() and form.cleaned_data["action"] == "activate_group":
        common_group_id = form.cleaned_data["common_group_id"]
        if not _can_manage_common_group(request.user, common_group_id):
            return HttpResponseForbidden(_("Accès refusé."))
        try:
            services.ensure_group_environment(common_group_id)
        except ValidationError as exc:
            messages.error(request, _validation_message(exc))
            return redirect("groups_manage")
        messages.success(request, _("L'espace AM du groupe est activé."))
        return redirect("group_detail", group_id=common_group_id)

    messages.error(request, _("Action groupe invalide."))
    return redirect("groups_manage")


def _handle_detail_post(request, common_group: CommonGroup, group: Group | None):
    return _handle_group_post(
        request,
        common_group,
        group,
        redirect_name="group_detail",
    )


def _group_management_page(request, group_id: int, page_key: str):
    if not request.user.is_authenticated:
        return redirect("login")

    common_group = _get_common_group(group_id)
    group = Group.objects.filter(gg_id=group_id).first()
    access_context = _build_group_access_context(request.user, common_group, group)
    if not access_context.can_manage_group:
        return HttpResponseForbidden(_("Accès refusé."))

    config = GROUP_PAGE_CONFIG[page_key]
    if group is None:
        messages.error(request, _("Activez l'espace AM avant cette action."))
        return redirect("group_detail", group_id=group_id)

    if request.method == "POST":
        return _handle_group_post(
            request,
            common_group,
            group,
            redirect_name=config["route"],
            allowed_actions=config["actions"],
        )

    context = _build_group_context(
        request,
        common_group,
        group,
        access_context=access_context,
    )
    context.update(
        {
            "page_key": page_key,
            "page_title": config["title"],
        }
    )
    return render(request, config["template"], context)


def _handle_group_post(
    request,
    common_group: CommonGroup,
    group: Group | None,
    *,
    redirect_name: str,
    allowed_actions: set[str] | None = None,
):
    action = request.POST.get("action", "").strip()
    group_id = common_group.group_id

    if action == "activate_group":
        try:
            services.ensure_group_environment(group_id)
        except ValidationError as exc:
            messages.error(request, _validation_message(exc))
        else:
            messages.success(request, _("L'espace AM du groupe est activé."))
        return redirect("group_detail", group_id=group_id)

    if group is None:
        messages.error(request, _("Activez l'espace AM avant cette action."))
        return redirect("group_detail", group_id=group_id)

    if allowed_actions is not None and action not in allowed_actions:
        messages.error(request, _("Action groupe invalide sur cette page."))
        return redirect(redirect_name, group_id=group_id)

    try:
        services.require_group_manager(request.user, group)
        _dispatch_group_action(request, group, action)
    except PermissionDenied:
        return HttpResponseForbidden(_("Accès refusé."))
    except (ValidationError, ValueError) as exc:
        messages.error(request, _validation_message(exc))

    return redirect(redirect_name, group_id=group_id)


def _dispatch_group_action(request, group: Group, action: str) -> None:
    if action in {"assign_responsable_impression", "remove_responsable_impression"}:
        form = forms.GroupMemberActionForm(request.POST)
        _validate_action_form(form, action)
        group_member = _get_group_member(group, form.cleaned_data["group_member_id"])
        if action == "assign_responsable_impression":
            services.assign_responsable_impression(group_member)
            messages.success(
                request, _("Le droit Responsable impression est attribué.")
            )
        else:
            services.remove_responsable_impression(group_member)
            messages.success(request, _("Le droit Responsable impression est retiré."))
        return

    if action == "set_common_responsable":
        form = forms.CommonResponsableForm(request.POST)
        _validate_action_form(form, action)
        services.set_common_responsable(
            group.gg_id,
            str(form.cleaned_data["member_id"]),
            enabled=form.cleaned_data["enabled"],
        )
        messages.success(request, _("Le rôle Responsable a été mis à jour."))
        return

    if action in {"remove_member_am_access", "remove_common_group_member"}:
        form = forms.MemberMembershipActionForm(request.POST)
        _validate_action_form(form, action)
        member_id = str(form.cleaned_data["member_id"])
        if action == "remove_member_am_access":
            services.remove_member_am_access(group.gg_id, member_id)
            messages.success(request, _("L'accès AM du membre est retiré."))
        else:
            services.remove_common_group_member(group.gg_id, member_id)
            messages.success(request, _("Le membre est retiré du groupe."))
        return

    if action in {"assign_function", "remove_function"}:
        form = forms.FunctionAssignmentForm(request.POST)
        _validate_action_form(form, action)
        group_member = _get_group_member(group, form.cleaned_data["group_member_id"])
        function = _get_group_function(group, form.cleaned_data["function_id"])
        if action == "assign_function":
            services.assign_group_function(group_member, function)
            messages.success(request, _("La fonction est attribuée."))
        else:
            services.remove_group_function(group_member, function)
            messages.success(request, _("La fonction est retirée."))
        return

    if action == "create_access_request":
        form = forms.AccessRequestForm(request.POST)
        _validate_action_form(form, action)
        member = Member(mm_id=form.cleaned_data["member_id"])
        services.create_access_request(
            group,
            member,
            consent_version=form.cleaned_data["consent_version"],
            consented_at=timezone.now(),
        )
        messages.success(request, _("La demande d'accès AM est créée."))
        return

    if action in {"accept_access_request", "refuse_access_request"}:
        form = forms.AccessRequestDecisionForm(request.POST)
        _validate_action_form(form, action)
        access_request = group.access_requests.get(
            pk=form.cleaned_data["access_request_id"]
        )
        if action == "accept_access_request":
            services.accept_access_request(access_request)
            messages.success(request, _("La demande d'accès AM est acceptée."))
        else:
            services.refuse_access_request(access_request)
            messages.success(request, _("La demande d'accès AM est refusée."))
        return

    if action in {"accept_common_join_request", "refuse_common_join_request"}:
        form = forms.CommonJoinRequestDecisionForm(request.POST)
        _validate_action_form(form, action)
        join_request = CommonGroupJoinRequest.objects.get(
            group_id=group.gg_id,
            member_id=form.cleaned_data["member_id"],
        )
        if action == "accept_common_join_request":
            services.accept_common_join_request(join_request)
            messages.success(request, _("La demande de rattachement est acceptée."))
        else:
            services.refuse_common_join_request(join_request)
            messages.success(request, _("La demande de rattachement est refusée."))
        return

    if action == "create_am_member_request":
        form = forms.AmMemberRequestForm(request.POST)
        _validate_action_form(form, action)
        requested_by = _current_group_member(group, request.user)
        token = secrets.token_urlsafe(24)
        services.create_am_member_request(
            group,
            requested_by,
            first_name=form.cleaned_data["first_name"],
            last_name=form.cleaned_data["last_name"],
            email=form.cleaned_data["email"],
            consent_token=token,
            consent_version=form.cleaned_data["consent_version"],
        )
        request.session[INVITATION_NOTICE_SESSION_KEY] = {
            "title": str(_("Invitation Membre AM")),
            "messageMarkdown": str(
                _(
                    "Transmettre ce jeton à la personne invitée :\n\n`%(token)s`\n\n"
                    "Il ne sera plus affiché après cette page."
                )
            )
            % {"token": token},
        }
        request.session.modified = True
        messages.success(request, _("La demande de Membre AM est créée."))
        return

    if action in {"refuse_am_member_request", "expire_am_member_request"}:
        form = forms.AmMemberRequestDecisionForm(request.POST)
        _validate_action_form(form, action)
        am_request = group.am_member_requests.get(
            pk=form.cleaned_data["am_member_request_id"]
        )
        if action == "refuse_am_member_request":
            services.refuse_am_member_request(am_request)
            messages.success(request, _("La demande de Membre AM est refusée."))
        else:
            services.expire_am_member_request(am_request, now=timezone.now())
            messages.success(request, _("La demande de Membre AM est expirée."))
        return

    if action == "accept_am_member_request":
        form = forms.AmMemberAcceptForm(request.POST)
        _validate_action_form(form, action)
        am_request = group.am_member_requests.get(
            pk=form.cleaned_data["am_member_request_id"]
        )
        services.accept_am_member_request(
            am_request,
            consent_token=form.cleaned_data["consent_token"],
            withdrawal_secret=form.cleaned_data["withdrawal_secret"],
        )
        messages.success(request, _("Le Membre AM est créé."))
        return

    if action == "save_function":
        form = forms.GroupFunctionForm(request.POST)
        _validate_action_form(form, action)
        function = _object_or_new(
            GroupFunction,
            group.functions,
            form.cleaned_data.get("object_id"),
            group=group,
        )
        _copy_fields(form, function, ["name", "position", "is_active"])
        function.auto_edit_celebration = form.cleaned_data["auto_edit_celebration"]
        services.save_group_function(function)
        messages.success(request, _("La fonction est enregistrée."))
        return

    if action == "save_group_settings":
        form = forms.GroupSettingsForm(request.POST)
        _validate_action_form(form, action)
        group.celebration_retention_months = form.cleaned_data[
            "celebration_retention_months"
        ]
        services.save_group_settings(group)
        messages.success(request, _("Les paramètres généraux sont enregistrés."))
        return

    if action == "save_am_member_title":
        form = forms.AmMemberTitleForm(request.POST)
        _validate_action_form(form, action)
        title = _object_or_new(
            AmMemberTitle,
            group.am_member_titles,
            form.cleaned_data.get("object_id"),
            group=group,
        )
        _copy_fields(form, title, ["label", "position", "is_active"])
        services.save_am_member_title(title)
        messages.success(request, _("Le titre Membre AM est enregistré."))
        return

    if action == "save_location":
        form = forms.GroupLocationForm(request.POST)
        _validate_action_form(form, action)
        location = _object_or_new(
            GroupLocation,
            group.locations,
            form.cleaned_data.get("object_id"),
            group=group,
        )
        _copy_fields(form, location, ["name", "address", "position", "is_active"])
        services.save_group_location(location)
        messages.success(request, _("Le lieu est enregistré."))
        return

    if action == "save_planning_state":
        form = forms.PlanningStateForm(request.POST)
        _validate_action_form(form, action)
        state = _object_or_new(
            PlanningState,
            group.planning_states,
            form.cleaned_data.get("object_id"),
            group=group,
        )
        _copy_fields(form, state, ["name", "color", "kind", "position", "is_active"])
        services.save_planning_state(state)
        messages.success(request, _("L'état planning est enregistré."))
        return

    if action == "create_celebration_rule":
        form = forms.CelebrationRuleForm(request.POST)
        _validate_action_form(form, action)
        services.create_celebration_rule(
            group,
            weekday=form.cleaned_data["weekday"],
            time=form.cleaned_data["time"],
            location=_get_location(group, form.cleaned_data["location_id"]),
            position=form.cleaned_data["position"],
            is_active=form.cleaned_data["is_active"],
        )
        messages.success(request, _("La règle régulière est créée."))
        return

    if action == "create_special_date_rule":
        form = forms.SpecialDateRuleForm(request.POST)
        _validate_action_form(form, action)
        services.create_special_date_rule(
            group,
            name=form.cleaned_data["name"],
            rule_type=form.cleaned_data["rule_type"],
            collision_mode=form.cleaned_data["collision_mode"],
            month=form.cleaned_data["month"],
            day=form.cleaned_data["day"],
            exact_date=form.cleaned_data["exact_date"],
            weekday=form.cleaned_data["weekday"],
            occurrence=form.cleaned_data["occurrence"],
            is_active=form.cleaned_data["is_active"],
        )
        messages.success(request, _("La date particulière est créée."))
        return

    if action == "add_song":
        form = forms.RepertoireSongForm(request.POST)
        _validate_action_form(form, action)
        services.add_song_to_repertoire(
            group,
            song_id=form.cleaned_data["song_id"],
            verse_ids=form.cleaned_data["verse_ids"],
        )
        messages.success(request, _("Le chant est ajouté au recueil."))
        return

    if action == "tag_song":
        form = forms.SongTagForm(request.POST)
        _validate_action_form(form, action)
        song = group.songs.get(pk=form.cleaned_data["song_id"])
        tag = CommonGroupTag.objects.get(
            pk=form.cleaned_data["group_tag_id"],
            group_id=group.gg_id,
        )
        services.tag_song(song, tag)
        messages.success(request, _("Le tag est associé au chant."))
        return

    if action == "set_tag_verse_selection":
        form = forms.SongTagVerseSelectionForm(request.POST)
        _validate_action_form(form, action)
        song_tag = SongTag.objects.get(
            pk=form.cleaned_data["song_tag_id"],
            song__group=group,
        )
        verse = Verse.objects.get(
            pk=form.cleaned_data["verse_id"],
            song=song_tag.song,
        )
        services.set_tag_verse_selection(
            song_tag,
            verse,
            selected_by_default=form.cleaned_data["selected_by_default"],
        )
        messages.success(request, _("La sélection du bloc est enregistrée."))
        return

    messages.error(request, _("Action groupe inconnue."))


def _build_group_access_context(user, common_group: CommonGroup, group: Group | None):
    is_authenticated = getattr(user, "is_authenticated", False)
    is_global_admin = bool(getattr(user, "is_admin", False))
    member_id = str(getattr(user, "external_id", "") or "").strip()
    membership = None
    if is_authenticated and member_id:
        membership = CommonGroupUser.objects.filter(
            group_id=common_group.group_id,
            member_id=member_id,
        ).first()

    has_am_access = bool(membership and membership.am_access)
    is_common_responsable = bool(membership and membership.is_group_admin)
    can_manage_group = is_global_admin or is_common_responsable
    can_enter_group = bool((group and has_am_access) or can_manage_group)
    return SimpleNamespace(
        membership=membership,
        member_id=member_id,
        has_am_access=has_am_access,
        is_common_responsable=is_common_responsable,
        is_global_admin=is_global_admin,
        can_manage_group=can_manage_group,
        can_enter_group=can_enter_group,
    )


def _build_group_context(
    request,
    common_group: CommonGroup,
    group: Group | None,
    *,
    access_context=None,
):
    invitation_notice = request.session.pop(INVITATION_NOTICE_SESSION_KEY, None)
    request.session.modified = True
    access_context = access_context or _build_group_access_context(
        request.user,
        common_group,
        group,
    )
    common_memberships = list(
        CommonGroupUser.objects.filter(group_id=common_group.group_id).order_by(
            "-is_group_admin",
            "member_id",
        )
    )

    context = {
        "common_group": common_group,
        "group": group,
        "selected_group": common_group,
        "common_memberships": common_memberships,
        "access_context": access_context,
        "invitation_notice_json": json.dumps(invitation_notice or {}),
        "forms": {
            "settings": forms.GroupSettingsForm(
                initial={
                    "action": "save_group_settings",
                    "celebration_retention_months": (
                        getattr(group, "celebration_retention_months", 24)
                        if group
                        else 24
                    ),
                }
            ),
            "access_request": forms.AccessRequestForm(
                initial={"action": "create_access_request"}
            ),
            "am_member_request": forms.AmMemberRequestForm(
                initial={"action": "create_am_member_request"}
            ),
            "function": forms.GroupFunctionForm(initial={"action": "save_function"}),
            "title": forms.AmMemberTitleForm(
                initial={"action": "save_am_member_title"}
            ),
            "location": forms.GroupLocationForm(initial={"action": "save_location"}),
            "planning_state": forms.PlanningStateForm(
                initial={"action": "save_planning_state"}
            ),
            "celebration_rule": forms.CelebrationRuleForm(
                initial={"action": "create_celebration_rule"}
            ),
            "special_date_rule": forms.SpecialDateRuleForm(
                initial={"action": "create_special_date_rule"}
            ),
            "song": forms.RepertoireSongForm(initial={"action": "add_song"}),
        },
    }
    if group is None:
        return context

    members = list(
        group.members.select_related("member", "am_profile")
        .prefetch_related("function_assignments__function", "role_assignments__role")
        .order_by("member_kind", "ggm_id")
    )
    songs = list(
        group.songs.prefetch_related(
            "verses",
            "song_tags__group_tag",
            "song_tags__verse_selections__verse",
        ).order_by("song_id")
    )
    common_join_requests = list(
        CommonGroupJoinRequest.objects.filter(group_id=group.gg_id).order_by(
            "member_id"
        )
    )
    access_requests = list(group.access_requests.all())
    member_profile_map = _directory_member_profile_map(
        [
            *(membership.member_id for membership in common_memberships),
            *(join_request.member_id for join_request in common_join_requests),
            *(access_request.member_id for access_request in access_requests),
        ]
    )
    account_member_rows = _build_account_member_rows(
        common_memberships,
        members,
        member_profile_map,
    )

    context.update(
        {
            "members": members,
            "account_members": [
                member
                for member in members
                if member.member_kind == MEMBER_KIND_ACCOUNT
            ],
            "account_member_rows": account_member_rows,
            "common_member_rows": _build_common_member_rows(
                common_memberships,
                member_profile_map,
            ),
            "function_member_rows": _build_function_member_rows(
                members,
                member_profile_map,
            ),
            "am_members": [
                member
                for member in members
                if member.member_kind != MEMBER_KIND_ACCOUNT
            ],
            "responsable_memberships": [
                membership
                for membership in common_memberships
                if membership.is_group_admin
            ],
            "responsable_member_rows": _build_responsable_member_rows(
                common_memberships,
                member_profile_map,
            ),
            "functions": list(group.functions.all()),
            "titles": list(group.am_member_titles.all()),
            "locations": list(group.locations.all()),
            "planning_states": list(group.planning_states.all()),
            "celebration_rules": list(group.celebration_rules.all()),
            "special_date_rules": list(group.special_date_rules.all()),
            "access_requests": access_requests,
            "access_request_rows": _build_member_request_rows(
                access_requests,
                member_profile_map,
            ),
            "common_join_requests": common_join_requests,
            "common_join_request_rows": _build_member_request_rows(
                common_join_requests,
                member_profile_map,
            ),
            "am_member_requests": list(group.am_member_requests.all()),
            "group_tags": list(
                CommonGroupTag.objects.filter(group_id=group.gg_id, is_active=True)
            ),
            "songs": songs,
            "metrics": {
                "members": len(members),
                "account_members": len(
                    [
                        membership
                        for membership in common_memberships
                        if membership.am_access
                    ]
                ),
                "am_members": len(
                    [
                        member
                        for member in members
                        if member.member_kind != MEMBER_KIND_ACCOUNT
                    ]
                ),
                "functions": group.functions.count(),
                "requests": group.access_requests.count()
                + CommonGroupJoinRequest.objects.filter(group_id=group.gg_id).count()
                + group.am_member_requests.filter(
                    status=AmMemberRequest.STATUS_PENDING
                ).count(),
                "songs": len(songs),
            },
        }
    )
    return context


def _directory_member_profile_map(member_ids):
    normalized_ids = sorted({str(member_id) for member_id in member_ids if member_id})
    if not normalized_ids:
        return {}

    try:
        records = list(DirectoryUserRecord.objects.filter(id__in=normalized_ids))
    except Exception:
        return {}

    return {
        str(record.id): {
            "first_name": record.first_name or "",
            "last_name": record.last_name or "",
            "username": record.username or "",
        }
        for record in records
    }


def _directory_display_name(member_id, profile_map):
    profile = profile_map.get(str(member_id), {})
    first_name = str(profile.get("first_name") or "").strip()
    last_name = str(profile.get("last_name") or "").strip()
    full_name = " ".join(part for part in [first_name, last_name] if part)
    if full_name:
        return full_name

    username = str(profile.get("username") or "").strip()
    if username:
        return username

    return _("Membre")


def _member_function_names(group_member):
    if group_member is None:
        return []

    assignments = getattr(group_member, "function_assignments", None)
    if assignments is None:
        return []

    return [
        assignment.function.name
        for assignment in assignments.all()
        if assignment.function and assignment.function.is_active
    ]


def _has_responsable_impression_role(group_member):
    if group_member is None:
        return False

    assignments = getattr(group_member, "role_assignments", None)
    if assignments is None:
        return False

    return any(
        assignment.role
        and assignment.role.code == ROLE_RESPONSABLE_IMPRESSION
        and assignment.role.is_active
        for assignment in assignments.all()
    )


def _build_account_member_rows(common_memberships, members, profile_map):
    account_members_by_member_id = {
        str(member.member_id): member
        for member in members
        if member.member_kind == MEMBER_KIND_ACCOUNT and member.member_id is not None
    }
    return [
        {
            "membership": membership,
            "group_member": account_members_by_member_id.get(str(membership.member_id)),
            "display_name": _directory_display_name(membership.member_id, profile_map),
            "is_responsable": membership.is_group_admin,
            "has_am_access": membership.am_access,
            "has_responsable_impression": _has_responsable_impression_role(
                account_members_by_member_id.get(str(membership.member_id))
            ),
            "function_names": _member_function_names(
                account_members_by_member_id.get(str(membership.member_id))
            ),
        }
        for membership in common_memberships
        if membership.am_access
    ]


def _build_responsable_member_rows(common_memberships, profile_map):
    return [
        {
            "membership": membership,
            "display_name": _directory_display_name(membership.member_id, profile_map),
            "has_am_access": membership.am_access,
        }
        for membership in common_memberships
        if membership.is_group_admin
    ]


def _build_common_member_rows(common_memberships, profile_map):
    return [
        {
            "membership": membership,
            "display_name": _directory_display_name(membership.member_id, profile_map),
            "has_am_access": membership.am_access,
            "is_responsable": membership.is_group_admin,
        }
        for membership in common_memberships
    ]


def _build_function_member_rows(members, profile_map):
    rows = []
    for member in members:
        if member.member_kind == MEMBER_KIND_ACCOUNT:
            display_name = _directory_display_name(member.member_id, profile_map)
            kind_label = _("Membre")
        else:
            display_name = " ".join(
                part
                for part in [
                    getattr(member.am_profile, "first_name", ""),
                    getattr(member.am_profile, "last_name", ""),
                ]
                if part
            )
            kind_label = _("Membre AM")

        rows.append(
            {
                "group_member": member,
                "display_name": display_name or kind_label,
                "kind_label": kind_label,
                "function_names": _member_function_names(member),
            }
        )
    return rows


def _build_member_request_rows(requests, profile_map):
    return [
        {
            "request": request,
            "display_name": _directory_display_name(request.member_id, profile_map),
        }
        for request in requests
    ]


def _manageable_common_groups(user):
    if getattr(user, "is_admin", False):
        return list(CommonGroup.objects.all().order_by("name", "group_id"))
    member_id = str(getattr(user, "external_id", "") or "").strip()
    group_ids = CommonGroupUser.objects.filter(
        member_id=member_id,
        is_group_admin=True,
    ).values("group_id")
    return list(
        CommonGroup.objects.filter(group_id__in=group_ids).order_by("name", "group_id")
    )


def _can_manage_common_group(user, group_id: int) -> bool:
    if getattr(user, "is_admin", False):
        return CommonGroup.objects.filter(group_id=group_id).exists()
    member_id = str(getattr(user, "external_id", "") or "").strip()
    return CommonGroupUser.objects.filter(
        group_id=group_id,
        member_id=member_id,
        is_group_admin=True,
    ).exists()


def _get_common_group(group_id: int) -> CommonGroup:
    try:
        return CommonGroup.objects.get(pk=group_id)
    except CommonGroup.DoesNotExist as exc:
        raise Http404 from exc


def _validate_action_form(form, expected_action: str) -> None:
    if not form.is_valid() or form.cleaned_data.get("action") != expected_action:
        raise ValidationError(_("Action invalide."))


def _get_group_member(group: Group, group_member_id: int) -> GroupMember:
    return group.members.get(pk=group_member_id)


def _get_group_function(group: Group, function_id: int) -> GroupFunction:
    return group.functions.get(pk=function_id)


def _get_location(group: Group, location_id: int) -> GroupLocation:
    return group.locations.get(pk=location_id)


def _current_group_member(group: Group, user) -> GroupMember:
    return group.members.get(
        member_id=str(getattr(user, "external_id", "") or "").strip(),
        member_kind=MEMBER_KIND_ACCOUNT,
    )


def _object_or_new(model, manager, object_id, **defaults):
    if object_id:
        return manager.get(pk=object_id)
    return model(**defaults)


def _copy_fields(form, instance, fields: list[str]) -> None:
    for field in fields:
        setattr(instance, field, form.cleaned_data[field])


def _validation_message(exc) -> str:
    if hasattr(exc, "messages"):
        return " ".join(str(message) for message in exc.messages)
    return str(exc)
