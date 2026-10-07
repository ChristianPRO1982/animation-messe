from __future__ import annotations

import json
import secrets

from django.contrib import messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import Http404, HttpResponseForbidden
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from app_group import forms, services
from app_group.models import (
    MEMBER_KIND_ACCOUNT,
    AmMemberRequest,
    AmMemberTitle,
    CommonGroup,
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
from app_member.models import Member

INVITATION_NOTICE_SESSION_KEY = "app_group_invitation_notice"


def groups_home(request):
    return render(request, "app_group/groups_home.html")


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
    if not _can_manage_common_group(request.user, group_id):
        return HttpResponseForbidden(_("Accès refusé."))

    if request.method == "POST":
        return _handle_detail_post(request, common_group, group)

    context = _build_group_context(request, common_group, group)
    return render(request, "app_group/group_detail.html", context)


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

    try:
        services.require_group_manager(request.user, group)
        _dispatch_group_action(request, group, action)
    except PermissionDenied:
        return HttpResponseForbidden(_("Accès refusé."))
    except (ValidationError, ValueError) as exc:
        messages.error(request, _validation_message(exc))

    return redirect("group_detail", group_id=group_id)


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


def _build_group_context(request, common_group: CommonGroup, group: Group | None):
    invitation_notice = request.session.pop(INVITATION_NOTICE_SESSION_KEY, None)
    request.session.modified = True
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
        "invitation_notice_json": json.dumps(invitation_notice or {}),
        "forms": {
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

    context.update(
        {
            "members": members,
            "functions": list(group.functions.all()),
            "titles": list(group.am_member_titles.all()),
            "locations": list(group.locations.all()),
            "planning_states": list(group.planning_states.all()),
            "celebration_rules": list(group.celebration_rules.all()),
            "special_date_rules": list(group.special_date_rules.all()),
            "access_requests": list(group.access_requests.all()),
            "am_member_requests": list(group.am_member_requests.all()),
            "group_tags": list(
                CommonGroupTag.objects.filter(group_id=group.gg_id, is_active=True)
            ),
            "songs": songs,
            "metrics": {
                "members": len(members),
                "functions": group.functions.count(),
                "requests": group.access_requests.count()
                + group.am_member_requests.filter(
                    status=AmMemberRequest.STATUS_PENDING
                ).count(),
                "songs": len(songs),
            },
        }
    )
    return context


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
