import importlib
import uuid
from datetime import time
from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import migrations
from django.http import Http404
from django.test import RequestFactory, SimpleTestCase
from django.urls import reverse
from django.utils import timezone

from app_group import forms as group_forms
from app_group import models as group_models
from app_group import services as group_services
from app_group import views as group_views
from app_member.models import Member

initial_migration = importlib.import_module("app_group.migrations.0001_initial")
second_migration = importlib.import_module(
    "app_group.migrations.0002_song_tag_common_group_tag_fk"
)
third_migration = importlib.import_module(
    "app_group.migrations.0003_common_group_tag_runtime_fields"
)
fourth_migration = importlib.import_module(
    "app_group.migrations.0004_group_contract_constraints"
)


def build_group(group_id=1):
    return group_models.Group(gg_id=group_id)


def build_member(member_id="11111111-1111-1111-1111-111111111111"):
    return Member(mm_id=uuid.UUID(member_id))


def build_group_member(*, group=None, member=None, member_kind=None):
    group = group or build_group()
    member_kind = member_kind or group_models.MEMBER_KIND_ACCOUNT
    return group_models.GroupMember(
        group=group,
        member=member if member_kind == group_models.MEMBER_KIND_ACCOUNT else None,
        member_kind=member_kind,
    )


class HelperSession(dict):
    modified = False


def build_request(factory, method="get", path="/groups/manage/", data=None, *, user):
    request = getattr(factory, method)(path, data=data or {})
    request.session = HelperSession()
    request.user = user
    request.LANGUAGE_CODE = "fr"
    return request


def build_user(*, authenticated=True, admin=False):
    return SimpleNamespace(
        is_authenticated=authenticated,
        is_admin=admin,
        external_id="11111111-1111-1111-1111-111111111111",
        username="tester",
    )


def build_access_context(*, can_enter=True, can_manage=True, has_am_access=True):
    return SimpleNamespace(
        membership=None,
        member_id="11111111-1111-1111-1111-111111111111",
        has_am_access=has_am_access,
        is_common_responsable=can_manage,
        is_global_admin=False,
        can_manage_group=can_manage,
        can_enter_group=can_enter,
    )


class AppGroupPublicPageTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    @patch("app_group.views._build_groups_home_context")
    def test_groups_home_is_public(self, home_context):
        home_context.return_value = {
            "rows": [],
            "selected_group": None,
            "is_authenticated": False,
        }
        request = build_request(
            self.factory,
            path="/groups/",
            user=build_user(authenticated=False),
        )

        response = group_views.groups_home(request)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Groupes")

    @patch("app_group.views._build_groups_home_context")
    def test_groups_home_uses_themed_groups_icon(self, home_context):
        home_context.return_value = {
            "rows": [],
            "selected_group": None,
            "is_authenticated": False,
        }
        request = build_request(
            self.factory,
            path="/groups/",
            user=build_user(authenticated=False),
        )

        response = group_views.groups_home(request)

        self.assertContains(response, 'data-theme-icon="groups"')
        self.assertContains(response, "icons/ui/normal/512/light/groups.png")
        self.assertContains(response, "icons/ui/normal/512/dark/groups.png")

    @patch("app_group.views._build_groups_home_context")
    def test_groups_home_shows_access_button_for_am_access_member(self, home_context):
        common_group = group_models.CommonGroup(
            group_id=7,
            name="Chorale",
            status=group_models.CommonGroup.STATUS_PRIVATE,
        )
        home_context.return_value = {
            "rows": [
                {
                    "common_group": common_group,
                    "is_member": True,
                    "has_am_access": True,
                    "is_responsable": False,
                    "can_enter_group": True,
                    "has_pending_request": False,
                    "has_pending_am_access_request": False,
                    "can_request_join": False,
                    "can_request_am_access": False,
                }
            ],
            "selected_group": None,
            "is_authenticated": True,
        }
        request = build_request(self.factory, path="/groups/", user=build_user())

        response = group_views.groups_home(request)

        self.assertContains(response, "Vous êtes membre de ce groupe.")
        self.assertContains(response, "Accéder au groupe")
        self.assertContains(response, reverse("group_detail", kwargs={"group_id": 7}))
        self.assertNotContains(response, "membre commun")
        self.assertNotContains(response, "Demander le rattachement")

    @patch("app_group.views._build_groups_home_context")
    def test_groups_home_shows_access_button_for_responsable_without_am_access(
        self, home_context
    ):
        common_group = group_models.CommonGroup(
            group_id=7,
            name="Chorale",
            status=group_models.CommonGroup.STATUS_PRIVATE,
        )
        home_context.return_value = {
            "rows": [
                {
                    "common_group": common_group,
                    "is_member": True,
                    "has_am_access": False,
                    "is_responsable": True,
                    "can_enter_group": True,
                    "has_pending_request": False,
                    "has_pending_am_access_request": False,
                    "can_request_join": False,
                    "can_request_am_access": False,
                }
            ],
            "selected_group": None,
            "is_authenticated": True,
        }
        request = build_request(self.factory, path="/groups/", user=build_user())

        response = group_views.groups_home(request)

        self.assertContains(response, "Accéder au groupe")
        self.assertContains(response, reverse("group_detail", kwargs={"group_id": 7}))

    @patch("app_group.views._build_groups_home_context")
    def test_groups_home_shows_am_access_request_for_member_without_am_access(
        self, home_context
    ):
        common_group = group_models.CommonGroup(
            group_id=7,
            name="Chorale",
            status=group_models.CommonGroup.STATUS_PRIVATE,
        )
        home_context.return_value = {
            "rows": [
                {
                    "common_group": common_group,
                    "is_member": True,
                    "has_am_access": False,
                    "is_responsable": False,
                    "can_enter_group": False,
                    "has_pending_request": False,
                    "has_pending_am_access_request": False,
                    "can_request_join": False,
                    "can_request_am_access": True,
                }
            ],
            "selected_group": None,
            "is_authenticated": True,
        }
        request = build_request(self.factory, path="/groups/", user=build_user())

        response = group_views.groups_home(request)

        self.assertContains(response, "Demander l’accès AM")
        self.assertContains(response, 'value="request_am_access"')
        self.assertNotContains(response, "Demander le rattachement")

    @patch("app_group.views._build_groups_home_context")
    def test_groups_home_shows_pending_am_access_request(self, home_context):
        common_group = group_models.CommonGroup(
            group_id=7,
            name="Chorale",
            status=group_models.CommonGroup.STATUS_PRIVATE,
        )
        home_context.return_value = {
            "rows": [
                {
                    "common_group": common_group,
                    "is_member": True,
                    "has_am_access": False,
                    "is_responsable": False,
                    "can_enter_group": False,
                    "has_pending_request": False,
                    "has_pending_am_access_request": True,
                    "can_request_join": False,
                    "can_request_am_access": False,
                }
            ],
            "selected_group": None,
            "is_authenticated": True,
        }
        request = build_request(self.factory, path="/groups/", user=build_user())

        response = group_views.groups_home(request)

        self.assertContains(response, "Demande d’accès AM en attente.")
        self.assertNotContains(response, "Demander l’accès AM")

    @patch("app_group.views.AccessRequest")
    @patch("app_group.views.CommonGroupJoinRequest")
    @patch("app_group.views.CommonGroupUser")
    @patch("app_group.views.CommonGroup")
    @patch("app_group.views.Group")
    def test_groups_home_context_lists_active_groups_with_requested_order(
        self,
        group_model,
        common_group_model,
        common_group_user,
        join_request_model,
        access_request_model,
    ):
        groups = [
            group_models.CommonGroup(
                group_id=1,
                name="Zulu privé",
                status=group_models.CommonGroup.STATUS_PRIVATE,
            ),
            group_models.CommonGroup(
                group_id=2,
                name="Alpha ouvert",
                status=group_models.CommonGroup.STATUS_OPEN,
            ),
            group_models.CommonGroup(
                group_id=3,
                name="Beta membre",
                status=group_models.CommonGroup.STATUS_PRIVATE,
            ),
        ]
        group_model.objects.values_list.return_value = [1, 2, 3]
        common_group_model.objects.filter.return_value.order_by.return_value = groups
        common_group_user.objects.filter.return_value = [
            SimpleNamespace(group_id=3, am_access=True, is_group_admin=False)
        ]
        join_request_model.objects.filter.return_value.values_list.return_value = [1]
        access_request_model.objects.filter.return_value.values_list.return_value = []
        request = build_request(self.factory, path="/groups/", user=build_user())

        context = group_views._build_groups_home_context(request)

        access_request_model.objects.filter.assert_called_once_with(
            member_id="11111111-1111-1111-1111-111111111111",
            request_type=group_models.REQUEST_TYPE_AM_ACCESS,
        )
        self.assertEqual(
            [row["common_group"].group_id for row in context["rows"]],
            [3, 2, 1],
        )
        self.assertTrue(context["rows"][0]["is_member"])
        self.assertTrue(context["rows"][0]["has_am_access"])
        self.assertTrue(context["rows"][0]["can_enter_group"])
        self.assertFalse(context["rows"][0]["can_request_am_access"])
        self.assertTrue(context["rows"][2]["has_pending_request"])

    @patch("app_group.views.AccessRequest")
    @patch("app_group.views.CommonGroupJoinRequest")
    @patch("app_group.views.CommonGroupUser")
    @patch("app_group.views.CommonGroup")
    @patch("app_group.views.Group")
    def test_groups_home_context_allows_responsable_to_enter_without_am_access(
        self,
        group_model,
        common_group_model,
        common_group_user,
        join_request_model,
        access_request_model,
    ):
        common_group = group_models.CommonGroup(
            group_id=7,
            name="Chorale",
            status=group_models.CommonGroup.STATUS_PRIVATE,
        )
        group_model.objects.values_list.return_value = [7]
        common_group_model.objects.filter.return_value.order_by.return_value = [
            common_group
        ]
        common_group_user.objects.filter.return_value = [
            SimpleNamespace(group_id=7, am_access=False, is_group_admin=True)
        ]
        join_request_model.objects.filter.return_value.values_list.return_value = []
        access_request_model.objects.filter.return_value.values_list.return_value = []
        request = build_request(self.factory, path="/groups/", user=build_user())

        context = group_views._build_groups_home_context(request)

        self.assertFalse(context["rows"][0]["has_am_access"])
        self.assertTrue(context["rows"][0]["is_responsable"])
        self.assertTrue(context["rows"][0]["can_enter_group"])

    @patch("app_group.views.AccessRequest")
    @patch("app_group.views.CommonGroupJoinRequest")
    @patch("app_group.views.CommonGroupUser")
    @patch("app_group.views.CommonGroup")
    @patch("app_group.views.Group")
    def test_groups_home_context_allows_am_access_request_for_member_without_am_access(
        self,
        group_model,
        common_group_model,
        common_group_user,
        join_request_model,
        access_request_model,
    ):
        common_group = group_models.CommonGroup(
            group_id=7,
            name="Chorale",
            status=group_models.CommonGroup.STATUS_PRIVATE,
        )
        group_model.objects.values_list.return_value = [7]
        common_group_model.objects.filter.return_value.order_by.return_value = [
            common_group
        ]
        common_group_user.objects.filter.return_value = [
            SimpleNamespace(group_id=7, am_access=False, is_group_admin=False)
        ]
        join_request_model.objects.filter.return_value.values_list.return_value = []
        access_request_model.objects.filter.return_value.values_list.return_value = []
        request = build_request(self.factory, path="/groups/", user=build_user())

        context = group_views._build_groups_home_context(request)

        self.assertTrue(context["rows"][0]["can_request_am_access"])

        access_request_model.objects.filter.return_value.values_list.return_value = [7]
        context = group_views._build_groups_home_context(request)

        self.assertTrue(context["rows"][0]["has_pending_am_access_request"])
        self.assertFalse(context["rows"][0]["can_request_am_access"])

    @patch("app_group.views.messages")
    @patch("app_group.views.services.create_common_join_request")
    def test_groups_home_post_creates_join_request_for_authenticated_user(
        self, create_join_request, _messages
    ):
        request = build_request(
            self.factory,
            method="post",
            path="/groups/",
            data={
                "action": "request_common_group_join",
                "common_group_id": "7",
            },
            user=build_user(),
        )

        response = group_views.groups_home(request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("groups_home"))
        create_join_request.assert_called_once_with(
            7,
            "11111111-1111-1111-1111-111111111111",
        )

    @patch("app_group.views.messages")
    @patch("app_group.views.services.create_access_request")
    @patch("app_group.views.Group")
    def test_groups_home_post_creates_am_access_request_for_authenticated_member(
        self, group_model, create_access_request, _messages
    ):
        group = group_models.Group(gg_id=7)
        group_model.objects.filter.return_value.first.return_value = group
        request = build_request(
            self.factory,
            method="post",
            path="/groups/",
            data={
                "action": "request_am_access",
                "common_group_id": "7",
            },
            user=build_user(),
        )

        response = group_views.groups_home(request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("groups_home"))
        create_access_request.assert_called_once()
        self.assertIs(create_access_request.call_args.args[0], group)
        self.assertEqual(
            str(create_access_request.call_args.args[1].mm_id),
            "11111111-1111-1111-1111-111111111111",
        )

    @patch("app_group.views.services.create_common_join_request")
    def test_groups_home_post_requires_authentication(self, create_join_request):
        request = build_request(
            self.factory,
            method="post",
            path="/groups/",
            data={
                "action": "request_common_group_join",
                "common_group_id": "7",
            },
            user=build_user(authenticated=False),
        )

        response = group_views.groups_home(request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("login"))
        create_join_request.assert_not_called()

    @patch("app_group.views.messages")
    @patch("app_group.views.services.create_common_join_request")
    def test_groups_home_post_reports_join_request_errors(
        self, create_join_request, message_api
    ):
        create_join_request.side_effect = ValidationError("refused")
        request = build_request(
            self.factory,
            method="post",
            path="/groups/",
            data={
                "action": "request_common_group_join",
                "common_group_id": "7",
            },
            user=build_user(),
        )

        response = group_views.groups_home(request)

        self.assertEqual(response.status_code, 302)
        message_api.error.assert_called_once()

    @patch("app_group.views.messages")
    def test_groups_home_post_rejects_invalid_actions_and_forms(self, message_api):
        invalid_join_request = build_request(
            self.factory,
            method="post",
            path="/groups/",
            data={"action": "request_common_group_join"},
            user=build_user(),
        )
        invalid_am_request = build_request(
            self.factory,
            method="post",
            path="/groups/",
            data={"action": "request_am_access"},
            user=build_user(),
        )
        unknown_request = build_request(
            self.factory,
            method="post",
            path="/groups/",
            data={"action": "nope"},
            user=build_user(),
        )

        self.assertEqual(group_views.groups_home(invalid_join_request).status_code, 302)
        self.assertEqual(group_views.groups_home(invalid_am_request).status_code, 302)
        self.assertEqual(group_views.groups_home(unknown_request).status_code, 302)
        self.assertEqual(message_api.error.call_count, 3)

    @patch("app_group.views.messages")
    @patch("app_group.views.Group")
    def test_groups_home_post_am_access_reports_missing_group(
        self, group_model, messages
    ):
        group_model.objects.filter.return_value.first.return_value = None
        request = build_request(
            self.factory,
            method="post",
            path="/groups/",
            data={
                "action": "request_am_access",
                "common_group_id": "7",
            },
            user=build_user(),
        )

        response = group_views.groups_home(request)

        self.assertEqual(response.status_code, 302)
        messages.error.assert_called_once()

    @patch("app_group.views.messages")
    @patch("app_group.views.services.create_access_request")
    @patch("app_group.views.Group")
    def test_groups_home_post_am_access_reports_service_error(
        self, group_model, create_access_request, messages
    ):
        group_model.objects.filter.return_value.first.return_value = build_group(7)
        create_access_request.side_effect = ValidationError("already active")
        request = build_request(
            self.factory,
            method="post",
            path="/groups/",
            data={
                "action": "request_am_access",
                "common_group_id": "7",
            },
            user=build_user(),
        )

        response = group_views.groups_home(request)

        self.assertEqual(response.status_code, 302)
        messages.error.assert_called_once()


class AppGroupManagementViewTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = build_user()
        self.common_group = group_models.CommonGroup(
            group_id=7,
            name="Chorale Saint Martin",
            status=group_models.CommonGroup.STATUS_OPEN,
        )
        self.group = group_models.Group(gg_id=7)

    def empty_group_context(self):
        return {
            "common_group": self.common_group,
            "group": self.group,
            "selected_group": self.common_group,
            "common_memberships": [],
            "access_context": build_access_context(),
            "responsable_memberships": [],
            "members": [],
            "account_members": [],
            "account_member_rows": [],
            "common_member_rows": [],
            "responsable_member_rows": [],
            "function_member_rows": [],
            "am_members": [],
            "functions": [],
            "titles": [],
            "locations": [],
            "planning_states": [],
            "celebration_rules": [],
            "special_date_rules": [],
            "access_requests": [],
            "access_request_rows": [],
            "common_join_requests": [],
            "common_join_request_rows": [],
            "am_member_requests": [],
            "group_tags": [],
            "songs": [],
            "metrics": {
                "members": 0,
                "account_members": 0,
                "am_members": 0,
                "requests": 0,
                "songs": 0,
                "functions": 0,
            },
            "invitation_notice_json": "{}",
            "forms": {
                "settings": group_forms.GroupSettingsForm(),
                "access_request": group_forms.AccessRequestForm(),
                "am_member_request": group_forms.AmMemberRequestForm(),
                "function": group_forms.GroupFunctionForm(),
                "title": group_forms.AmMemberTitleForm(),
                "location": group_forms.GroupLocationForm(),
                "planning_state": group_forms.PlanningStateForm(),
                "celebration_rule": group_forms.CelebrationRuleForm(),
                "special_date_rule": group_forms.SpecialDateRuleForm(),
                "song": group_forms.RepertoireSongForm(),
            },
        }

    def test_manage_requires_authentication(self):
        request = build_request(
            self.factory,
            user=build_user(authenticated=False),
        )

        response = group_views.groups_manage(request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("login"))

    @patch("app_group.views.Group")
    @patch("app_group.views._manageable_common_groups")
    def test_manage_lists_responsable_groups_with_activation_state(
        self, manageable_groups, group_model
    ):
        request = build_request(self.factory, user=self.user)
        manageable_groups.return_value = [self.common_group]
        group_model.objects.filter.return_value.values_list.return_value = []

        response = group_views.groups_manage(request)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Chorale Saint Martin")
        self.assertContains(response, reverse("group_detail", kwargs={"group_id": 7}))
        self.assertContains(response, 'data-app-group-confirm="')

    @patch("app_group.views._build_group_access_context")
    @patch("app_group.views.Group")
    @patch("app_group.views._get_common_group")
    def test_detail_forbids_user_without_group_access(
        self, get_common_group, group_model, build_access
    ):
        request = build_request(
            self.factory,
            path="/groups/7/",
            user=self.user,
        )
        get_common_group.return_value = self.common_group
        group_model.objects.filter.return_value.first.return_value = self.group
        build_access.return_value = build_access_context(
            can_enter=False,
            can_manage=False,
            has_am_access=False,
        )

        response = group_views.group_detail(request, 7)

        self.assertEqual(response.status_code, 403)

    @patch("app_group.views._build_group_context")
    @patch("app_group.views._build_group_access_context")
    @patch("app_group.views.Group")
    @patch("app_group.views._get_common_group")
    def test_detail_template_contains_management_sections_and_popup_hooks(
        self,
        get_common_group,
        group_model,
        build_access,
        build_context,
    ):
        request = build_request(
            self.factory,
            path="/groups/7/",
            user=self.user,
        )
        get_common_group.return_value = self.common_group
        group_model.objects.filter.return_value.first.return_value = self.group
        build_access.return_value = build_access_context()
        build_context.return_value = {
            "common_group": self.common_group,
            "group": self.group,
            "selected_group": self.common_group,
            "common_memberships": [],
            "access_context": build_access.return_value,
            "members": [],
            "account_member_rows": [],
            "common_member_rows": [],
            "responsable_member_rows": [],
            "function_member_rows": [],
            "functions": [],
            "titles": [],
            "locations": [],
            "planning_states": [],
            "celebration_rules": [],
            "special_date_rules": [],
            "access_requests": [],
            "access_request_rows": [],
            "common_join_requests": [],
            "common_join_request_rows": [],
            "am_member_requests": [],
            "group_tags": [],
            "songs": [],
            "metrics": {
                "members": 0,
                "account_members": 0,
                "am_members": 0,
                "requests": 2,
                "songs": 0,
                "functions": 0,
            },
            "invitation_notice_json": "{}",
            "forms": {
                "settings": group_forms.GroupSettingsForm(),
                "access_request": group_forms.AccessRequestForm(),
                "am_member_request": group_forms.AmMemberRequestForm(),
                "function": group_forms.GroupFunctionForm(),
                "title": group_forms.AmMemberTitleForm(),
                "location": group_forms.GroupLocationForm(),
                "planning_state": group_forms.PlanningStateForm(),
                "celebration_rule": group_forms.CelebrationRuleForm(),
                "special_date_rule": group_forms.SpecialDateRuleForm(),
                "song": group_forms.RepertoireSongForm(),
            },
        }

        response = group_views.group_detail(request, 7)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Liste des membres")
        self.assertContains(response, "Liste des responsables")
        self.assertContains(response, "Liste des Membres AM")
        self.assertContains(response, reverse("group_songs", kwargs={"group_id": 7}))
        self.assertContains(response, "🆕 2 demandes en cours.", count=2)
        self.assertContains(
            response,
            reverse("group_members", kwargs={"group_id": 7}),
        )
        self.assertContains(response, "static/js/app_group.js")
        self.assertNotContains(response, "Créer une demande d’accès AM")
        self.assertNotContains(response, "Ajouter au recueil")

    @patch("app_group.views._build_group_context")
    @patch("app_group.views._build_group_access_context")
    @patch("app_group.views.Group")
    @patch("app_group.views._get_common_group")
    def test_detail_for_member_hides_management_actions(
        self,
        get_common_group,
        group_model,
        build_access,
        build_context,
    ):
        request = build_request(
            self.factory,
            path="/groups/7/",
            user=self.user,
        )
        access_context = build_access_context(can_manage=False, has_am_access=True)
        get_common_group.return_value = self.common_group
        group_model.objects.filter.return_value.first.return_value = self.group
        build_access.return_value = access_context
        context = self.empty_group_context()
        context["access_context"] = access_context
        context["metrics"]["requests"] = 2
        context["account_member_rows"] = [
            {
                "membership": SimpleNamespace(
                    member_id="11111111-1111-1111-1111-111111111111"
                ),
                "group_member": SimpleNamespace(ggm_id=5),
                "display_name": "Alice Martin",
                "has_am_access": True,
                "is_responsable": False,
                "has_responsable_impression": False,
                "function_names": [],
            }
        ]
        build_context.return_value = context

        response = group_views.group_detail(request, 7)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Liste des membres")
        self.assertContains(response, "Alice Martin")
        self.assertNotContains(response, "11111111-1111-1111-1111-111111111111")
        self.assertNotContains(response, "Modifier les personnes")
        self.assertNotContains(response, "Paramètres du calendrier")
        self.assertNotContains(response, "Paramètres du groupe")
        self.assertNotContains(response, "Gestion des chants")
        self.assertNotContains(response, "🆕 2 demandes en cours.")

    @patch("app_group.views._get_common_group")
    def test_dedicated_pages_redirect_anonymous_user(self, get_common_group):
        dedicated_views = [
            group_views.group_members,
            group_views.group_responsables,
            group_views.group_am_members,
            group_views.group_functions,
            group_views.group_am_member_titles,
            group_views.group_calendar_states,
            group_views.group_calendar_regular_rules,
            group_views.group_calendar_special_dates,
            group_views.group_settings,
            group_views.group_locations,
            group_views.group_songs,
        ]

        for view_func in dedicated_views:
            with self.subTest(view=view_func.__name__):
                request = build_request(
                    self.factory,
                    path="/groups/7/members/",
                    user=build_user(authenticated=False),
                )

                response = view_func(request, 7)

                self.assertEqual(response.status_code, 302)
                self.assertEqual(response.url, reverse("login"))

        get_common_group.assert_not_called()

    @patch("app_group.views._build_group_access_context")
    @patch("app_group.views.Group")
    @patch("app_group.views._get_common_group")
    def test_dedicated_page_forbids_non_responsable(
        self, get_common_group, group_model, build_access
    ):
        request = build_request(
            self.factory,
            path="/groups/7/members/",
            user=self.user,
        )
        get_common_group.return_value = self.common_group
        group_model.objects.filter.return_value.first.return_value = self.group
        build_access.return_value = build_access_context(can_manage=False)

        response = group_views.group_members(request, 7)

        self.assertEqual(response.status_code, 403)

    @patch("app_group.views.messages")
    @patch("app_group.views._build_group_access_context")
    @patch("app_group.views.Group")
    @patch("app_group.views._get_common_group")
    def test_dedicated_page_redirects_to_dashboard_when_am_inactive(
        self, get_common_group, group_model, build_access, message_api
    ):
        request = build_request(
            self.factory,
            path="/groups/7/members/",
            user=self.user,
        )
        get_common_group.return_value = self.common_group
        group_model.objects.filter.return_value.first.return_value = None
        build_access.return_value = build_access_context(can_manage=True)

        response = group_views.group_members(request, 7)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("group_detail", kwargs={"group_id": 7}))
        message_api.error.assert_called_once()

    @patch("app_group.views._build_group_context")
    @patch("app_group.views._build_group_access_context")
    @patch("app_group.views.Group")
    @patch("app_group.views._get_common_group")
    def test_dedicated_pages_render_expected_templates(
        self,
        get_common_group,
        group_model,
        build_access,
        build_context,
    ):
        pages = [
            (group_views.group_members, "group_members", "Membres avec compte"),
            (group_views.group_responsables, "group_responsables", "Responsables"),
            (
                group_views.group_am_members,
                "group_am_members",
                "Créer une demande Membre AM",
            ),
            (group_views.group_functions, "group_functions", "Affectations"),
            (
                group_views.group_am_member_titles,
                "group_am_member_titles",
                "Titres Membre AM",
            ),
            (
                group_views.group_calendar_states,
                "group_calendar_states",
                "États planning",
            ),
            (
                group_views.group_calendar_regular_rules,
                "group_calendar_regular_rules",
                "Règles régulières",
            ),
            (
                group_views.group_calendar_special_dates,
                "group_calendar_special_dates",
                "Dates particulières",
            ),
            (group_views.group_settings, "group_settings", "Paramètres généraux"),
            (group_views.group_locations, "group_locations", "Lieux"),
            (group_views.group_songs, "group_songs", "Ajouter un chant LSS"),
        ]
        get_common_group.return_value = self.common_group
        group_model.objects.filter.return_value.first.return_value = self.group
        build_access.return_value = build_access_context()

        for view_func, route_name, expected_text in pages:
            with self.subTest(route=route_name):
                request = build_request(
                    self.factory,
                    path=reverse(route_name, kwargs={"group_id": 7}),
                    user=self.user,
                )
                build_context.return_value = self.empty_group_context()

                response = view_func(request, 7)

                self.assertEqual(response.status_code, 200)
                self.assertContains(response, expected_text)
                self.assertContains(
                    response, reverse("group_detail", kwargs={"group_id": 7})
                )
                self.assertContains(response, "static/js/app_group.js")

    @patch("app_group.views._build_group_context")
    @patch("app_group.views._build_group_access_context")
    @patch("app_group.views.Group")
    @patch("app_group.views._get_common_group")
    def test_responsables_page_uses_full_width_inline_rows(
        self,
        get_common_group,
        group_model,
        build_access,
        build_context,
    ):
        request = build_request(
            self.factory,
            path=reverse("group_responsables", kwargs={"group_id": 7}),
            user=self.user,
        )
        context = self.empty_group_context()
        context["common_member_rows"] = [
            {
                "membership": SimpleNamespace(
                    member_id="11111111-1111-1111-1111-111111111111"
                ),
                "display_name": "Alice Martin",
                "is_responsable": False,
                "has_am_access": True,
            }
        ]
        get_common_group.return_value = self.common_group
        group_model.objects.filter.return_value.first.return_value = self.group
        build_access.return_value = build_access_context()
        build_context.return_value = context

        response = group_views.group_responsables(request, 7)

        self.assertContains(response, "group-single-column")
        self.assertContains(response, 'class="group-responsable-row"')
        self.assertContains(response, "Alice Martin")
        self.assertContains(response, "Nommer Responsable")

    @patch("app_group.views._build_group_context")
    @patch("app_group.views._build_group_access_context")
    @patch("app_group.views.Group")
    @patch("app_group.views._get_common_group")
    def test_members_page_summary_and_removal_actions(
        self,
        get_common_group,
        group_model,
        build_access,
        build_context,
    ):
        request = build_request(
            self.factory,
            path=reverse("group_members", kwargs={"group_id": 7}),
            user=self.user,
        )
        context = self.empty_group_context()
        context["metrics"]["account_members"] = 1
        context["metrics"]["requests"] = 0
        context["account_member_rows"] = [
            {
                "membership": SimpleNamespace(
                    member_id="11111111-1111-1111-1111-111111111111"
                ),
                "group_member": SimpleNamespace(ggm_id=5),
                "display_name": "Alice Martin",
                "has_am_access": True,
                "is_responsable": False,
                "has_responsable_impression": False,
                "function_names": [],
            }
        ]
        get_common_group.return_value = self.common_group
        group_model.objects.filter.return_value.first.return_value = self.group
        build_access.return_value = build_access_context()
        build_context.return_value = context

        response = group_views.group_members(request, 7)

        self.assertContains(response, "1 membres avec compte.")
        self.assertContains(response, "0 demandes en attente.")
        self.assertContains(response, "⚖️")
        self.assertContains(response, "🖨️")
        self.assertContains(response, "⛪")
        self.assertContains(response, "👥")
        self.assertContains(response, 'class="group-member-grid"')
        self.assertContains(response, 'class="group-member-grid-row"')
        self.assertContains(response, 'type="checkbox"')
        self.assertContains(
            response, 'class="site-action site-action--danger group-member-icon-action"'
        )
        self.assertContains(response, 'data-app-group-confirm="')
        self.assertNotContains(response, "Créer une demande d’accès AM")
        self.assertNotContains(response, "Accès AM</span>")
        self.assertNotContains(response, "Fonctions :")

    @patch("app_group.views.messages")
    @patch("app_group.views.services.ensure_group_environment")
    @patch("app_group.views._build_group_access_context")
    @patch("app_group.views.Group")
    @patch("app_group.views._get_common_group")
    def test_detail_post_activates_group_environment(
        self,
        get_common_group,
        group_model,
        build_access,
        ensure_environment,
        _messages,
    ):
        request = build_request(
            self.factory,
            method="post",
            path="/groups/7/",
            data={"action": "activate_group"},
            user=self.user,
        )
        get_common_group.return_value = self.common_group
        group_model.objects.filter.return_value.first.return_value = None
        build_access.return_value = build_access_context(can_manage=True)

        response = group_views.group_detail(request, 7)

        self.assertEqual(response.status_code, 302)
        ensure_environment.assert_called_once_with(7)

    @patch("app_group.views.messages")
    @patch("app_group.views.services.assign_responsable_impression")
    @patch("app_group.views.services.require_group_manager")
    @patch("app_group.views._get_group_member")
    @patch("app_group.views._build_group_access_context")
    @patch("app_group.views.Group")
    @patch("app_group.views._get_common_group")
    def test_detail_post_assigns_responsable_impression_via_service(
        self,
        get_common_group,
        group_model,
        build_access,
        get_group_member,
        _require_manager,
        assign_responsable,
        _messages,
    ):
        group_member = build_group_member(group=self.group, member=build_member())
        get_group_member.return_value = group_member
        request = build_request(
            self.factory,
            method="post",
            path="/groups/7/members/",
            data={
                "action": "assign_responsable_impression",
                "group_member_id": "42",
            },
            user=self.user,
        )
        get_common_group.return_value = self.common_group
        group_model.objects.filter.return_value.first.return_value = self.group
        build_access.return_value = build_access_context()

        response = group_views.group_members(request, 7)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("group_members", kwargs={"group_id": 7}))
        assign_responsable.assert_called_once_with(group_member)

    @patch("app_group.views.messages")
    @patch("app_group.views.services.set_common_responsable")
    @patch("app_group.views.services.require_group_manager")
    @patch("app_group.views._build_group_access_context")
    @patch("app_group.views.Group")
    @patch("app_group.views._get_common_group")
    def test_detail_post_updates_common_responsable_via_service(
        self,
        get_common_group,
        group_model,
        build_access,
        _require_manager,
        set_common_responsable,
        _messages,
    ):
        request = build_request(
            self.factory,
            method="post",
            path="/groups/7/responsables/",
            data={
                "action": "set_common_responsable",
                "member_id": "22222222-2222-2222-2222-222222222222",
                "enabled": "on",
            },
            user=self.user,
        )
        get_common_group.return_value = self.common_group
        group_model.objects.filter.return_value.first.return_value = self.group
        build_access.return_value = build_access_context()

        response = group_views.group_responsables(request, 7)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url, reverse("group_responsables", kwargs={"group_id": 7})
        )
        set_common_responsable.assert_called_once_with(
            7,
            "22222222-2222-2222-2222-222222222222",
            enabled=True,
        )

    @patch("app_group.views.messages")
    @patch("app_group.views.services.create_am_member_request")
    @patch("app_group.views.secrets.token_urlsafe", return_value="token-public")
    @patch("app_group.views._current_group_member")
    @patch("app_group.views.services.require_group_manager")
    @patch("app_group.views._build_group_access_context")
    @patch("app_group.views.Group")
    @patch("app_group.views._get_common_group")
    def test_detail_post_creates_am_member_request_without_storing_raw_token_in_form(
        self,
        get_common_group,
        group_model,
        build_access,
        _require_manager,
        current_group_member,
        _token,
        create_request,
        _messages,
    ):
        requested_by = build_group_member(group=self.group, member=build_member())
        current_group_member.return_value = requested_by
        request = build_request(
            self.factory,
            method="post",
            path="/groups/7/am-members/",
            data={
                "action": "create_am_member_request",
                "first_name": "Alice",
                "last_name": "Martin",
                "email": "alice@example.test",
                "consent_version": "v1",
            },
            user=self.user,
        )
        get_common_group.return_value = self.common_group
        group_model.objects.filter.return_value.first.return_value = self.group
        build_access.return_value = build_access_context()

        response = group_views.group_am_members(request, 7)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url, reverse("group_am_members", kwargs={"group_id": 7})
        )
        create_request.assert_called_once()
        self.assertEqual(
            create_request.call_args.kwargs["consent_token"], "token-public"
        )
        self.assertIn(
            "token-public",
            request.session["app_group_invitation_notice"]["messageMarkdown"],
        )

    @patch("app_group.views.messages")
    @patch("app_group.views.services.assign_group_function")
    @patch("app_group.views.services.require_group_manager")
    @patch("app_group.views._get_group_function")
    @patch("app_group.views._get_group_member")
    @patch("app_group.views._build_group_access_context")
    @patch("app_group.views.Group")
    @patch("app_group.views._get_common_group")
    def test_detail_post_assigns_functions_to_am_members_via_service(
        self,
        get_common_group,
        group_model,
        build_access,
        get_group_member,
        get_group_function,
        _require_manager,
        assign_function,
        _messages,
    ):
        group_member = build_group_member(
            group=self.group, member_kind=group_models.MEMBER_KIND_AM
        )
        function = group_models.GroupFunction(group=self.group, name="Chantre")
        get_group_member.return_value = group_member
        get_group_function.return_value = function
        request = build_request(
            self.factory,
            method="post",
            path="/groups/7/functions/",
            data={
                "action": "assign_function",
                "group_member_id": "42",
                "function_id": "5",
            },
            user=self.user,
        )
        get_common_group.return_value = self.common_group
        group_model.objects.filter.return_value.first.return_value = self.group
        build_access.return_value = build_access_context()

        response = group_views.group_functions(request, 7)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url, reverse("group_functions", kwargs={"group_id": 7})
        )
        assign_function.assert_called_once_with(group_member, function)

    @patch("app_group.views.messages")
    @patch("app_group.views.services.add_song_to_repertoire")
    @patch("app_group.views.services.require_group_manager")
    @patch("app_group.views._build_group_access_context")
    @patch("app_group.views.Group")
    @patch("app_group.views._get_common_group")
    def test_detail_post_adds_song_to_repertoire_via_service(
        self,
        get_common_group,
        group_model,
        build_access,
        _require_manager,
        add_song,
        _messages,
    ):
        request = build_request(
            self.factory,
            method="post",
            path="/groups/7/songs/",
            data={
                "action": "add_song",
                "song_id": "123",
                "verse_ids": "1, 2 3",
            },
            user=self.user,
        )
        get_common_group.return_value = self.common_group
        group_model.objects.filter.return_value.first.return_value = self.group
        build_access.return_value = build_access_context()

        response = group_views.group_songs(request, 7)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("group_songs", kwargs={"group_id": 7}))
        add_song.assert_called_once_with(self.group, song_id=123, verse_ids=[1, 2, 3])


class AppGroupManagementDispatchCoverageTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = build_user()
        self.common_group = group_models.CommonGroup(group_id=7, name="Chorale")
        self.group = group_models.Group(gg_id=7)

    def post_request(self, data):
        return build_request(
            self.factory,
            method="post",
            path="/groups/7/",
            data=data,
            user=self.user,
        )

    @patch("app_group.views.messages")
    @patch("app_group.views._can_manage_common_group", return_value=False)
    def test_manage_post_forbids_unmanageable_group(self, _can_manage, _messages):
        request = self.post_request(
            {"action": "activate_group", "common_group_id": "7"}
        )

        response = group_views._handle_manage_post(request)

        self.assertEqual(response.status_code, 403)

    @patch("app_group.views.messages")
    def test_manage_post_rejects_invalid_action(self, message_api):
        request = self.post_request({"action": "nope", "common_group_id": "7"})

        response = group_views._handle_manage_post(request)

        self.assertEqual(response.status_code, 302)
        message_api.error.assert_called_once()

    @patch("app_group.views.messages")
    @patch("app_group.views.services.ensure_group_environment")
    @patch("app_group.views._can_manage_common_group", return_value=True)
    def test_manage_post_reports_activation_validation_error(
        self, _can_manage, ensure_environment, message_api
    ):
        ensure_environment.side_effect = ValidationError("missing")
        request = self.post_request(
            {"action": "activate_group", "common_group_id": "7"}
        )

        response = group_views._handle_manage_post(request)

        self.assertEqual(response.status_code, 302)
        message_api.error.assert_called_once()

    @patch("app_group.views._get_common_group")
    def test_group_detail_redirects_anonymous_user(self, get_common_group):
        request = build_request(
            self.factory,
            path="/groups/7/",
            user=build_user(authenticated=False),
        )

        response = group_views.group_detail(request, 7)

        self.assertEqual(response.status_code, 302)
        get_common_group.assert_not_called()

    @patch("app_group.views.messages")
    @patch("app_group.views.services.ensure_group_environment")
    def test_detail_post_activation_success_and_error(
        self, ensure_environment, messages
    ):
        request = self.post_request({"action": "activate_group"})

        response = group_views._handle_detail_post(request, self.common_group, None)

        self.assertEqual(response.status_code, 302)
        messages.success.assert_called_once()

        ensure_environment.side_effect = ValidationError("bad")
        request = self.post_request({"action": "activate_group"})

        response = group_views._handle_detail_post(request, self.common_group, None)

        self.assertEqual(response.status_code, 302)
        messages.error.assert_called_once()

    @patch("app_group.views.messages")
    def test_group_post_rejects_action_not_allowed_on_page(self, message_api):
        request = self.post_request({"action": "save_function"})

        response = group_views._handle_group_post(
            request,
            self.common_group,
            self.group,
            redirect_name="group_members",
            allowed_actions={"remove_member_am_access"},
        )

        self.assertEqual(response.status_code, 302)
        message_api.error.assert_called_once()

    @patch("app_group.views.messages")
    def test_detail_post_requires_active_am_group_for_other_actions(self, message_api):
        request = self.post_request({"action": "save_function", "name": "Chantre"})

        response = group_views._handle_detail_post(request, self.common_group, None)

        self.assertEqual(response.status_code, 302)
        message_api.error.assert_called_once()

    @patch("app_group.views.messages")
    @patch("app_group.views.services.require_group_manager")
    def test_detail_post_handles_permission_and_validation_errors(
        self, require_manager, message_api
    ):
        require_manager.side_effect = PermissionDenied()
        request = self.post_request({"action": "unknown"})

        response = group_views._handle_detail_post(
            request, self.common_group, self.group
        )

        self.assertEqual(response.status_code, 403)

        require_manager.side_effect = None
        request = self.post_request({"action": "assign_function"})

        response = group_views._handle_detail_post(
            request, self.common_group, self.group
        )

        self.assertEqual(response.status_code, 302)
        message_api.error.assert_called_once()

    @patch("app_group.views.messages")
    @patch("app_group.views.services.save_group_settings")
    def test_dispatch_saves_group_settings(self, save_group_settings, _messages):
        request = self.post_request(
            {"action": "save_group_settings", "celebration_retention_months": "12"}
        )

        group_views._dispatch_group_action(request, self.group, "save_group_settings")

        self.assertEqual(self.group.celebration_retention_months, 12)
        save_group_settings.assert_called_once_with(self.group)

    def test_repertoire_song_form_rejects_invalid_verse_ids(self):
        bad_text = group_forms.RepertoireSongForm(
            {"action": "add_song", "song_id": "1", "verse_ids": "abc"}
        )
        bad_negative = group_forms.RepertoireSongForm(
            {"action": "add_song", "song_id": "1", "verse_ids": "-2"}
        )

        self.assertFalse(bad_text.is_valid())
        self.assertFalse(bad_negative.is_valid())

    @patch("app_group.views.messages")
    @patch("app_group.views.services.remove_responsable_impression")
    @patch("app_group.views._get_group_member")
    def test_dispatch_removes_responsable_impression(
        self, get_group_member, remove_responsable, _messages
    ):
        group_member = build_group_member(group=self.group, member=build_member())
        get_group_member.return_value = group_member
        request = self.post_request(
            {"action": "remove_responsable_impression", "group_member_id": "1"}
        )

        group_views._dispatch_group_action(
            request, self.group, "remove_responsable_impression"
        )

        remove_responsable.assert_called_once_with(group_member)

    @patch("app_group.views.messages")
    @patch("app_group.views.services.remove_group_function")
    @patch("app_group.views._get_group_function")
    @patch("app_group.views._get_group_member")
    def test_dispatch_removes_function(
        self, get_group_member, get_function, remove_function, _messages
    ):
        group_member = build_group_member(group=self.group, member=build_member())
        function = group_models.GroupFunction(group=self.group, name="Chantre")
        get_group_member.return_value = group_member
        get_function.return_value = function
        request = self.post_request(
            {
                "action": "remove_function",
                "group_member_id": "1",
                "function_id": "2",
            }
        )

        group_views._dispatch_group_action(request, self.group, "remove_function")

        remove_function.assert_called_once_with(group_member, function)

    @patch("app_group.views.messages")
    @patch("app_group.views.services.create_access_request")
    def test_dispatch_creates_access_request(self, create_access_request, _messages):
        request = self.post_request(
            {
                "action": "create_access_request",
                "member_id": "22222222-2222-2222-2222-222222222222",
                "consent_version": "v1",
            }
        )

        group_views._dispatch_group_action(request, self.group, "create_access_request")

        create_access_request.assert_called_once()
        self.assertEqual(create_access_request.call_args.args[0], self.group)
        self.assertEqual(
            str(create_access_request.call_args.args[1].mm_id),
            "22222222-2222-2222-2222-222222222222",
        )

    @patch("app_group.views.messages")
    @patch("app_group.views.services.refuse_access_request")
    @patch("app_group.views.services.accept_access_request")
    def test_dispatch_access_request_decisions(
        self, accept_access_request, refuse_access_request, _messages
    ):
        access_request = object()
        group = SimpleNamespace(gg_id=7, access_requests=Mock())
        group.access_requests.get.return_value = access_request

        accept_request = self.post_request(
            {"action": "accept_access_request", "access_request_id": "4"}
        )
        refuse_request = self.post_request(
            {"action": "refuse_access_request", "access_request_id": "4"}
        )

        group_views._dispatch_group_action(
            accept_request, group, "accept_access_request"
        )
        group_views._dispatch_group_action(
            refuse_request, group, "refuse_access_request"
        )

        accept_access_request.assert_called_once_with(access_request)
        refuse_access_request.assert_called_once_with(access_request)

    @patch("app_group.views.messages")
    @patch("app_group.views.services.remove_common_group_member")
    @patch("app_group.views.services.remove_member_am_access")
    def test_dispatch_member_removals(
        self, remove_am_access, remove_common_member, _messages
    ):
        remove_am_request = self.post_request(
            {
                "action": "remove_member_am_access",
                "member_id": "22222222-2222-2222-2222-222222222222",
            }
        )
        remove_common_request = self.post_request(
            {
                "action": "remove_common_group_member",
                "member_id": "22222222-2222-2222-2222-222222222222",
            }
        )

        group_views._dispatch_group_action(
            remove_am_request, self.group, "remove_member_am_access"
        )
        group_views._dispatch_group_action(
            remove_common_request, self.group, "remove_common_group_member"
        )

        remove_am_access.assert_called_once_with(
            7, "22222222-2222-2222-2222-222222222222"
        )
        remove_common_member.assert_called_once_with(
            7, "22222222-2222-2222-2222-222222222222"
        )

    @patch("app_group.views.messages")
    @patch("app_group.views.services.refuse_common_join_request")
    @patch("app_group.views.services.accept_common_join_request")
    @patch("app_group.views.CommonGroupJoinRequest")
    def test_dispatch_common_join_request_decisions(
        self,
        join_request_model,
        accept_join_request,
        refuse_join_request,
        _messages,
    ):
        join_request = object()
        join_request_model.objects.get.return_value = join_request
        accept_request = self.post_request(
            {
                "action": "accept_common_join_request",
                "member_id": "22222222-2222-2222-2222-222222222222",
            }
        )
        refuse_request = self.post_request(
            {
                "action": "refuse_common_join_request",
                "member_id": "22222222-2222-2222-2222-222222222222",
            }
        )

        group_views._dispatch_group_action(
            accept_request, self.group, "accept_common_join_request"
        )
        group_views._dispatch_group_action(
            refuse_request, self.group, "refuse_common_join_request"
        )

        accept_join_request.assert_called_once_with(join_request)
        refuse_join_request.assert_called_once_with(join_request)

    @patch("app_group.views.messages")
    @patch("app_group.views.services.expire_am_member_request")
    @patch("app_group.views.services.refuse_am_member_request")
    def test_dispatch_am_member_request_refuse_and_expire(
        self, refuse_request, expire_request, _messages
    ):
        am_request = object()
        group = SimpleNamespace(gg_id=7, am_member_requests=Mock())
        group.am_member_requests.get.return_value = am_request

        refuse_post = self.post_request(
            {"action": "refuse_am_member_request", "am_member_request_id": "5"}
        )
        expire_post = self.post_request(
            {"action": "expire_am_member_request", "am_member_request_id": "5"}
        )

        group_views._dispatch_group_action(
            refuse_post, group, "refuse_am_member_request"
        )
        group_views._dispatch_group_action(
            expire_post, group, "expire_am_member_request"
        )

        refuse_request.assert_called_once_with(am_request)
        expire_request.assert_called_once()

    @patch("app_group.views.messages")
    @patch("app_group.views.services.accept_am_member_request")
    def test_dispatch_accepts_am_member_request(self, accept_request, _messages):
        am_request = object()
        group = SimpleNamespace(gg_id=7, am_member_requests=Mock())
        group.am_member_requests.get.return_value = am_request
        request = self.post_request(
            {
                "action": "accept_am_member_request",
                "am_member_request_id": "5",
                "consent_token": "token",
                "withdrawal_secret": "secret",
            }
        )

        group_views._dispatch_group_action(request, group, "accept_am_member_request")

        accept_request.assert_called_once_with(
            am_request, consent_token="token", withdrawal_secret="secret"
        )

    @patch("app_group.views.messages")
    @patch("app_group.views._object_or_new")
    @patch("app_group.views.services.save_planning_state")
    @patch("app_group.views.services.save_group_location")
    @patch("app_group.views.services.save_am_member_title")
    @patch("app_group.views.services.save_group_function")
    def test_dispatch_saves_group_parameter_objects(
        self,
        save_function,
        save_title,
        save_location,
        save_state,
        object_or_new,
        _messages,
    ):
        object_or_new.side_effect = [
            group_models.GroupFunction(group=self.group),
            group_models.AmMemberTitle(group=self.group),
            group_models.GroupLocation(group=self.group),
            group_models.PlanningState(group=self.group),
        ]
        payloads = [
            (
                "save_function",
                {
                    "name": "Chantre",
                    "position": "1",
                    "is_active": "on",
                    "auto_edit_celebration": "on",
                },
            ),
            (
                "save_am_member_title",
                {"label": "Ami", "position": "2", "is_active": "on"},
            ),
            (
                "save_location",
                {
                    "name": "Eglise",
                    "address": "Place",
                    "position": "3",
                    "is_active": "on",
                },
            ),
            (
                "save_planning_state",
                {
                    "name": "Disponible",
                    "color": "#123456",
                    "kind": group_models.PLANNING_STATE_SELECTION,
                    "position": "4",
                    "is_active": "on",
                },
            ),
        ]

        for action, data in payloads:
            with self.subTest(action=action):
                request = self.post_request({"action": action, **data})
                group_views._dispatch_group_action(request, self.group, action)

        save_function.assert_called_once()
        save_title.assert_called_once()
        save_location.assert_called_once()
        save_state.assert_called_once()

    @patch("app_group.views.messages")
    @patch("app_group.views.services.create_special_date_rule")
    @patch("app_group.views.services.create_celebration_rule")
    @patch("app_group.views._get_location")
    def test_dispatch_creates_rule_objects(
        self, get_location, create_celebration_rule, create_special_date_rule, _messages
    ):
        location = group_models.GroupLocation(group=self.group, name="Eglise")
        get_location.return_value = location

        celebration_request = self.post_request(
            {
                "action": "create_celebration_rule",
                "weekday": "7",
                "time": "10:30",
                "location_id": "1",
                "position": "0",
                "is_active": "on",
            }
        )
        special_date_request = self.post_request(
            {
                "action": "create_special_date_rule",
                "name": "Noel",
                "rule_type": group_models.SpecialDateRule.RULE_ANNUAL_FIXED,
                "collision_mode": group_models.SpecialDateRule.COLLISION_ADD,
                "month": "12",
                "day": "25",
                "is_active": "on",
            }
        )

        group_views._dispatch_group_action(
            celebration_request, self.group, "create_celebration_rule"
        )
        group_views._dispatch_group_action(
            special_date_request, self.group, "create_special_date_rule"
        )

        create_celebration_rule.assert_called_once()
        create_special_date_rule.assert_called_once()

    @patch("app_group.views.messages")
    @patch("app_group.views.services.set_tag_verse_selection")
    @patch("app_group.views.services.tag_song")
    @patch("app_group.views.CommonGroupTag")
    @patch("app_group.views.SongTag")
    @patch("app_group.views.Verse")
    def test_dispatch_tag_song_and_selection(
        self,
        verse_model,
        song_tag_model,
        common_group_tag_model,
        tag_song,
        set_selection,
        _messages,
    ):
        song = group_models.Song(group=self.group, song_id=12)
        tag = group_models.CommonGroupTag(gt_id=2, group_id=7, name="Entree")
        song_tag = group_models.SongTag(song=song, group_tag=tag)
        verse = group_models.Verse(song=song, verse_id=1)
        group = SimpleNamespace(gg_id=7, songs=Mock())
        group.songs.get.return_value = song
        common_group_tag_model.objects.get.return_value = tag
        song_tag_model.objects.get.return_value = song_tag
        verse_model.objects.get.return_value = verse

        tag_request = self.post_request(
            {"action": "tag_song", "song_id": "1", "group_tag_id": "2"}
        )
        selection_request = self.post_request(
            {
                "action": "set_tag_verse_selection",
                "song_tag_id": "3",
                "verse_id": "4",
                "selected_by_default": "on",
            }
        )

        group_views._dispatch_group_action(tag_request, group, "tag_song")
        group_views._dispatch_group_action(
            selection_request, group, "set_tag_verse_selection"
        )

        tag_song.assert_called_once_with(song, tag)
        set_selection.assert_called_once_with(song_tag, verse, selected_by_default=True)

    @patch("app_group.views.CommonGroupJoinRequest")
    @patch("app_group.views.CommonGroupTag")
    @patch("app_group.views.CommonGroupUser")
    def test_build_group_context_for_inactive_and_active_group(
        self, common_group_user, common_group_tag, common_join_request
    ):
        request = self.post_request({})
        request.session[group_views.INVITATION_NOTICE_SESSION_KEY] = {
            "messageMarkdown": "token"
        }
        common_group_user.objects.filter.return_value.order_by.return_value = []

        inactive_context = group_views._build_group_context(
            request, self.common_group, None
        )

        self.assertIsNone(inactive_context["group"])
        self.assertIn("token", inactive_context["invitation_notice_json"])

        manager = Mock()
        manager.all.return_value = []
        manager.count.return_value = 0
        manager.filter.return_value.count.return_value = 0
        members = Mock()
        members.select_related.return_value.prefetch_related.return_value.order_by.return_value = []
        songs = Mock()
        songs.prefetch_related.return_value.order_by.return_value = []
        group = SimpleNamespace(
            gg_id=7,
            members=members,
            songs=songs,
            functions=manager,
            am_member_titles=manager,
            locations=manager,
            planning_states=manager,
            celebration_rules=manager,
            special_date_rules=manager,
            access_requests=manager,
            am_member_requests=manager,
        )
        common_group_tag.objects.filter.return_value = []
        common_join_request.objects.filter.return_value.order_by.return_value = []
        common_join_request.objects.filter.return_value.count.return_value = 0

        active_context = group_views._build_group_context(
            request, self.common_group, group
        )

        self.assertEqual(active_context["metrics"]["members"], 0)
        self.assertEqual(active_context["metrics"]["requests"], 0)

    @patch("app_group.views.DirectoryUserRecord")
    def test_directory_member_profile_map_and_display_name_fallbacks(
        self, directory_model
    ):
        member_id = uuid.UUID("11111111-1111-1111-1111-111111111111")
        directory_model.objects.filter.return_value = [
            SimpleNamespace(
                id=member_id,
                first_name="Alice",
                last_name="Martin",
                username="alice",
            )
        ]

        profile_map = group_views._directory_member_profile_map([member_id])

        self.assertEqual(
            group_views._directory_display_name(member_id, profile_map),
            "Alice Martin",
        )
        self.assertEqual(group_views._directory_member_profile_map([]), {})

        directory_model.objects.filter.side_effect = RuntimeError("missing table")
        self.assertEqual(group_views._directory_member_profile_map([member_id]), {})

        self.assertEqual(
            group_views._directory_display_name(
                member_id,
                {str(member_id): {"username": "fallback"}},
            ),
            "fallback",
        )
        self.assertEqual(
            str(group_views._directory_display_name(member_id, {})), "Membre"
        )

    def test_member_row_helpers_cover_roles_and_functions(self):
        active_function = SimpleNamespace(name="Chantre", is_active=True)
        inactive_function = SimpleNamespace(name="Archive", is_active=False)
        role = SimpleNamespace(
            code=group_models.ROLE_RESPONSABLE_IMPRESSION,
            is_active=True,
        )
        group_member = SimpleNamespace(
            member_kind=group_models.MEMBER_KIND_ACCOUNT,
            member_id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
            function_assignments=Mock(
                all=Mock(
                    return_value=[
                        SimpleNamespace(function=active_function),
                        SimpleNamespace(function=inactive_function),
                    ]
                )
            ),
            role_assignments=Mock(all=Mock(return_value=[SimpleNamespace(role=role)])),
        )
        am_member = SimpleNamespace(
            member_kind=group_models.MEMBER_KIND_AM,
            am_profile=SimpleNamespace(first_name="Bob", last_name="Durand"),
            function_assignments=Mock(all=Mock(return_value=[])),
        )
        profile_map = {
            "11111111-1111-1111-1111-111111111111": {
                "first_name": "Alice",
                "last_name": "Martin",
            }
        }

        self.assertEqual(
            group_views._member_function_names(group_member),
            ["Chantre"],
        )
        self.assertTrue(group_views._has_responsable_impression_role(group_member))
        self.assertEqual(group_views._member_function_names(None), [])
        self.assertFalse(group_views._has_responsable_impression_role(None))

        rows = group_views._build_function_member_rows(
            [group_member, am_member],
            profile_map,
        )

        self.assertEqual(rows[0]["display_name"], "Alice Martin")
        self.assertEqual(rows[0]["function_names"], ["Chantre"])
        self.assertEqual(rows[1]["display_name"], "Bob Durand")

    @patch("app_group.views.CommonGroup")
    @patch("app_group.views.CommonGroupUser")
    def test_group_access_helpers_cover_admin_and_responsable_paths(
        self, common_group_user, common_group_model
    ):
        admin = build_user(admin=True)
        common_group_model.objects.all.return_value.order_by.return_value = [
            self.common_group
        ]
        common_group_model.objects.filter.return_value.exists.return_value = True
        common_group_user.objects.filter.return_value.values.return_value = [7]
        common_group_model.objects.filter.return_value.order_by.return_value = [
            self.common_group
        ]

        self.assertEqual(
            group_views._manageable_common_groups(admin), [self.common_group]
        )
        self.assertTrue(group_views._can_manage_common_group(admin, 7))
        self.assertEqual(
            group_views._manageable_common_groups(build_user()), [self.common_group]
        )

    @patch("app_group.views.CommonGroup")
    def test_get_common_group_and_small_helpers(self, common_group_model):
        common_group_model.objects.get.return_value = self.common_group
        self.assertIs(group_views._get_common_group(7), self.common_group)

        common_group_model.DoesNotExist = group_models.CommonGroup.DoesNotExist
        common_group_model.objects.get.side_effect = common_group_model.DoesNotExist
        with self.assertRaises(Http404):
            group_views._get_common_group(8)

        manager = Mock()
        existing = object()
        manager.get.return_value = existing
        self.assertIs(group_views._object_or_new(object, manager, 1), existing)
        created = group_views._object_or_new(group_models.Group, manager, None, gg_id=9)
        self.assertEqual(created.gg_id, 9)

        form = SimpleNamespace(cleaned_data={"name": "Chantre"})
        target = SimpleNamespace()
        group_views._copy_fields(form, target, ["name"])
        self.assertEqual(target.name, "Chantre")
        self.assertEqual(group_views._validation_message(ValueError("bad")), "bad")


class AppGroupModelContractTests(SimpleTestCase):
    def test_common_group_models_are_unmanaged_external_tables(self):
        expected_tables = {
            group_models.CommonGroup: 'common"."g_groups',
            group_models.CommonGroupUser: 'common"."g_group_user',
            group_models.CommonGroupJoinRequest: ('common"."g_group_user_ask_to_join'),
            group_models.CommonGroupTag: 'common"."group_tags',
        }

        for model, db_table in expected_tables.items():
            with self.subTest(model=model.__name__):
                self.assertFalse(model._meta.managed)
                self.assertEqual(model._meta.db_table, db_table)

    def test_common_membership_models_use_composite_primary_keys(self):
        self.assertEqual(
            group_models.CommonGroupUser._meta.pk.field_names,
            ("group_id", "member_id"),
        )
        self.assertEqual(
            group_models.CommonGroupJoinRequest._meta.pk.field_names,
            ("group_id", "member_id"),
        )

    def test_common_group_tag_model_matches_common_runtime_table(self):
        fields = {
            field.name: field for field in group_models.CommonGroupTag._meta.fields
        }

        self.assertEqual(fields["gt_id"].primary_key, True)
        self.assertEqual(fields["group_id"].column, "group_id")
        self.assertEqual(fields["name"].max_length, 255)
        self.assertEqual(fields["sort_order"].default, 0)
        self.assertEqual(fields["is_active"].default, True)

    def test_group_is_am_extension_without_open_mode_copy(self):
        fields = {field.name for field in group_models.Group._meta.fields}

        self.assertEqual(group_models.Group._meta.db_table, 'am"."g_group')
        self.assertIn("gg_id", fields)
        self.assertIn("celebration_retention_months", fields)
        self.assertNotIn("is_open", fields)

    def test_group_member_keeps_single_am_anchor_and_member_kinds(self):
        fields = {field.name: field for field in group_models.GroupMember._meta.fields}
        constraint_names = {
            constraint.name for constraint in group_models.GroupMember._meta.constraints
        }

        self.assertEqual(fields["ggm_id"].primary_key, True)
        self.assertEqual(fields["member"].column, "mm_id")
        self.assertEqual(fields["member"].db_constraint, False)
        self.assertEqual(
            set(dict(group_models.GroupMember.MEMBER_KIND_CHOICES)),
            {group_models.MEMBER_KIND_ACCOUNT, group_models.MEMBER_KIND_AM},
        )
        self.assertIn("g_group_member_kind_member_valid", constraint_names)
        self.assertIn("g_group_member_account_unique", constraint_names)

    def test_responsable_is_not_an_am_role_code(self):
        self.assertEqual(
            group_models.GroupRole.SYSTEM_ROLE_CODES,
            frozenset({group_models.ROLE_RESPONSABLE_IMPRESSION}),
        )
        self.assertNotIn("responsable", group_models.GroupRole.SYSTEM_ROLE_CODES)

    def test_model_contains_contract_constraints_for_group_parameters(self):
        celebration_constraints = {
            constraint.name
            for constraint in group_models.CelebrationRule._meta.constraints
        }
        special_date_constraints = {
            constraint.name
            for constraint in group_models.SpecialDateRule._meta.constraints
        }

        self.assertIn("g_celebration_rule_weekday_valid", celebration_constraints)
        self.assertIn("g_celebration_rule_active_slot_unique", celebration_constraints)
        self.assertIn("g_special_date_rule_month_valid", special_date_constraints)
        self.assertIn("g_special_date_rule_day_valid", special_date_constraints)
        self.assertIn("g_special_date_rule_weekday_valid", special_date_constraints)


class AppGroupServiceTests(SimpleTestCase):
    def test_secret_and_email_helpers_never_return_raw_values(self):
        encoded = group_services.hash_personal_secret("secret-value")

        self.assertNotEqual(encoded, "secret-value")
        self.assertTrue(group_services.check_personal_secret("secret-value", encoded))
        self.assertFalse(group_services.check_personal_secret("bad", encoded))
        self.assertNotIn(
            "alice@example.test", group_services.email_fingerprint("Alice@Example.Test")
        )

        with self.assertRaises(ValidationError):
            group_services.hash_personal_secret("")
        with self.assertRaises(ValidationError):
            group_services.email_fingerprint("")

    @patch("app_group.services.is_common_group_responsable")
    def test_group_management_permissions_accept_admin_or_responsable(
        self, is_responsable
    ):
        group = build_group(7)
        admin_user = SimpleNamespace(
            is_authenticated=True,
            is_admin=True,
            external_id="11111111-1111-1111-1111-111111111111",
        )
        responsable_user = SimpleNamespace(
            is_authenticated=True,
            is_admin=False,
            external_id="22222222-2222-2222-2222-222222222222",
        )
        anonymous = SimpleNamespace(is_authenticated=False, is_admin=False)

        self.assertTrue(group_services.can_manage_group(admin_user, group))
        is_responsable.return_value = True
        self.assertTrue(group_services.can_manage_group(responsable_user, group))
        self.assertFalse(group_services.can_manage_group(anonymous, group))

        is_responsable.return_value = False
        with self.assertRaises(PermissionDenied):
            group_services.require_group_manager(responsable_user, group)

    def test_private_user_member_id_requires_external_id(self):
        with self.assertRaises(PermissionDenied):
            group_services._user_member_id(SimpleNamespace(external_id=""))

    @patch("app_group.services.can_manage_group", return_value=True)
    def test_require_group_manager_accepts_authorized_user(self, _can_manage_group):
        group_services.require_group_manager(build_user(), build_group())

    @patch("app_group.services.CommonGroupUser")
    def test_common_responsable_lookup_uses_common_membership(self, common_group_user):
        common_group_user.objects.filter.return_value.exists.return_value = True

        self.assertTrue(
            group_services.is_common_group_responsable(
                1,
                "11111111-1111-1111-1111-111111111111",
            )
        )

    @patch("app_group.services.Group")
    @patch("app_group.services.CommonGroup")
    def test_ensure_group_environment_requires_common_group_and_creates_extension(
        self, common_group, group_model
    ):
        common_group.objects.filter.return_value.exists.return_value = False

        with self.assertRaises(ValidationError):
            group_services.ensure_group_environment(1)

        group = build_group(1)
        common_group.objects.filter.return_value.exists.return_value = True
        group_model.objects.get_or_create.return_value = (group, True)

        self.assertIs(group_services.ensure_group_environment(1), group)
        group_model.objects.get_or_create.assert_called_once_with(
            gg_id=1,
            defaults={"celebration_retention_months": 24},
        )

    @patch("app_group.services.transaction.atomic")
    @patch("app_group.services.CommonGroupUser")
    def test_last_common_responsable_is_protected(self, common_group_user, atomic):
        atomic.return_value.__enter__ = Mock(return_value=None)
        atomic.return_value.__exit__ = Mock(return_value=False)
        memberships = Mock()
        memberships.filter.side_effect = [
            Mock(count=Mock(return_value=1)),
            Mock(exists=Mock(return_value=True)),
        ]
        common_group_user.objects.select_for_update.return_value.filter.return_value = (
            memberships
        )

        with self.assertRaisesMessage(ValidationError, "au moins un Responsable"):
            group_services.set_common_responsable(
                1,
                "11111111-1111-1111-1111-111111111111",
                enabled=False,
            )

        common_group_user.objects.select_for_update.assert_called_once()

    @patch("app_group.services.transaction.atomic")
    @patch("app_group.services.CommonGroupUser")
    def test_set_common_responsable_updates_existing_membership(
        self, common_group_user, atomic
    ):
        atomic.return_value.__enter__ = Mock(return_value=None)
        atomic.return_value.__exit__ = Mock(return_value=False)
        memberships = Mock()
        memberships.filter.return_value.update.return_value = 1
        common_group_user.objects.select_for_update.return_value.filter.return_value = (
            memberships
        )

        group_services.set_common_responsable(
            1,
            "11111111-1111-1111-1111-111111111111",
            enabled=True,
        )

        memberships.filter.assert_called_once_with(
            member_id="11111111-1111-1111-1111-111111111111"
        )

    @patch("app_group.services.transaction.atomic")
    @patch("app_group.services.CommonGroupUser")
    def test_set_common_responsable_requires_existing_membership(
        self, common_group_user, atomic
    ):
        atomic.return_value.__enter__ = Mock(return_value=None)
        atomic.return_value.__exit__ = Mock(return_value=False)
        memberships = Mock()
        memberships.filter.return_value.update.return_value = 0
        common_group_user.objects.select_for_update.return_value.filter.return_value = (
            memberships
        )

        with self.assertRaises(ValidationError):
            group_services.set_common_responsable(
                1,
                "11111111-1111-1111-1111-111111111111",
                enabled=True,
            )

    @patch("app_group.services.GroupMember")
    @patch("app_group.services.transaction.atomic")
    @patch("app_group.services.CommonGroupUser")
    def test_remove_member_am_access_disables_am_and_deletes_anchor(
        self, common_group_user, atomic, group_member_model
    ):
        atomic.return_value.__enter__ = Mock(return_value=None)
        atomic.return_value.__exit__ = Mock(return_value=False)
        membership = Mock(is_group_admin=False, am_access=True)
        memberships = Mock()
        memberships.filter.return_value.first.return_value = membership
        common_group_user.objects.select_for_update.return_value.filter.return_value = (
            memberships
        )
        group_member_model.objects.filter.return_value.delete.return_value = (1, {})

        group_services.remove_member_am_access(
            1, "11111111-1111-1111-1111-111111111111"
        )

        self.assertFalse(membership.am_access)
        membership.save.assert_called_once_with(update_fields=["am_access"])
        group_member_model.objects.filter.assert_called_once_with(
            group_id=1,
            member_id="11111111-1111-1111-1111-111111111111",
            member_kind=group_models.MEMBER_KIND_ACCOUNT,
        )
        group_member_model.objects.filter.return_value.delete.assert_called_once()

    @patch("app_group.services.GroupMember")
    @patch("app_group.services.transaction.atomic")
    @patch("app_group.services.CommonGroupUser")
    def test_remove_member_am_access_accepts_missing_anchor_and_inactive_access(
        self, common_group_user, atomic, group_member_model
    ):
        atomic.return_value.__enter__ = Mock(return_value=None)
        atomic.return_value.__exit__ = Mock(return_value=False)
        membership = Mock(is_group_admin=False, am_access=False)
        memberships = Mock()
        memberships.filter.return_value.first.return_value = membership
        common_group_user.objects.select_for_update.return_value.filter.return_value = (
            memberships
        )
        group_member_model.objects.filter.return_value.delete.return_value = (0, {})

        group_services.remove_member_am_access(
            1, "11111111-1111-1111-1111-111111111111"
        )

        membership.save.assert_not_called()
        group_member_model.objects.filter.return_value.delete.assert_called_once()

    @patch("app_group.services.GroupMember")
    @patch("app_group.services.transaction.atomic")
    @patch("app_group.services.CommonGroupUser")
    def test_member_removals_require_existing_common_membership(
        self, common_group_user, atomic, _group_member_model
    ):
        atomic.return_value.__enter__ = Mock(return_value=None)
        atomic.return_value.__exit__ = Mock(return_value=False)
        memberships = Mock()
        memberships.filter.return_value.first.return_value = None
        common_group_user.objects.select_for_update.return_value.filter.return_value = (
            memberships
        )

        with self.assertRaisesMessage(ValidationError, "introuvable"):
            group_services.remove_member_am_access(
                1, "11111111-1111-1111-1111-111111111111"
            )
        with self.assertRaisesMessage(ValidationError, "introuvable"):
            group_services.remove_common_group_member(
                1, "11111111-1111-1111-1111-111111111111"
            )

    @patch("app_group.services.GroupMember")
    @patch("app_group.services.transaction.atomic")
    @patch("app_group.services.CommonGroupUser")
    def test_remove_common_group_member_deletes_membership_and_anchor(
        self, common_group_user, atomic, group_member_model
    ):
        atomic.return_value.__enter__ = Mock(return_value=None)
        atomic.return_value.__exit__ = Mock(return_value=False)
        membership = Mock(is_group_admin=False)
        memberships = Mock()
        memberships.filter.return_value.first.return_value = membership
        common_group_user.objects.select_for_update.return_value.filter.return_value = (
            memberships
        )
        group_member_model.objects.filter.return_value.delete.return_value = (1, {})

        group_services.remove_common_group_member(
            1, "11111111-1111-1111-1111-111111111111"
        )

        group_member_model.objects.filter.return_value.delete.assert_called_once()
        membership.delete.assert_called_once()

    @patch("app_group.services.GroupMember")
    @patch("app_group.services.transaction.atomic")
    @patch("app_group.services.CommonGroupUser")
    def test_member_removals_protect_last_responsable(
        self, common_group_user, atomic, _group_member_model
    ):
        atomic.return_value.__enter__ = Mock(return_value=None)
        atomic.return_value.__exit__ = Mock(return_value=False)
        membership = Mock(is_group_admin=True, am_access=True)
        memberships = Mock()
        memberships.filter.side_effect = [
            Mock(first=Mock(return_value=membership)),
            Mock(count=Mock(return_value=1)),
            Mock(first=Mock(return_value=membership)),
            Mock(count=Mock(return_value=1)),
        ]
        common_group_user.objects.select_for_update.return_value.filter.return_value = (
            memberships
        )

        with self.assertRaisesMessage(ValidationError, "au moins un Responsable"):
            group_services.remove_member_am_access(
                1, "11111111-1111-1111-1111-111111111111"
            )
        with self.assertRaisesMessage(ValidationError, "au moins un Responsable"):
            group_services.remove_common_group_member(
                1, "11111111-1111-1111-1111-111111111111"
            )

    @patch("app_group.services.GroupMemberRole")
    @patch("app_group.services.ensure_responsable_impression_role")
    def test_responsable_impression_is_for_account_members_only(
        self, ensure_role, member_role_model
    ):
        group = build_group()
        role = group_models.GroupRole(
            group=group, code=group_models.ROLE_RESPONSABLE_IMPRESSION
        )
        account_member = build_group_member(group=group, member=build_member())
        am_member = build_group_member(
            group=group, member_kind=group_models.MEMBER_KIND_AM
        )
        assignment = object()
        ensure_role.return_value = role
        member_role_model.objects.get_or_create.return_value = (assignment, True)

        self.assertIs(
            group_services.assign_responsable_impression(account_member), assignment
        )
        with self.assertRaises(ValidationError):
            group_services.assign_responsable_impression(am_member)

    @patch("app_group.services.GroupRole")
    def test_responsable_impression_role_is_normalized_when_existing(self, role_model):
        group = build_group()
        role = Mock(is_system=False, is_active=False, label="Ancien libelle")
        role_model.objects.get_or_create.return_value = (role, False)

        self.assertIs(group_services.ensure_responsable_impression_role(group), role)

        self.assertTrue(role.is_system)
        self.assertTrue(role.is_active)
        self.assertEqual(str(role.label), "Responsable impression")
        role.save.assert_called_once_with(
            update_fields=["is_system", "is_active", "label"]
        )

    @patch("app_group.services.GroupRole")
    def test_responsable_impression_role_unchanged_when_normalized(self, role_model):
        group = build_group()
        role = Mock(is_system=True, is_active=True, label="Responsable impression")
        role_model.objects.get_or_create.return_value = (role, False)

        self.assertIs(group_services.ensure_responsable_impression_role(group), role)

        role.save.assert_not_called()

    @patch("app_group.services.GroupMemberRole")
    @patch("app_group.services.ensure_responsable_impression_role")
    def test_remove_responsable_impression_deletes_assignment(
        self, ensure_role, member_role_model
    ):
        group = build_group()
        role = group_models.GroupRole(
            group=group, code=group_models.ROLE_RESPONSABLE_IMPRESSION
        )
        group_member = build_group_member(group=group, member=build_member())
        ensure_role.return_value = role
        member_role_model.objects.filter.return_value.delete.return_value = (1, {})

        self.assertEqual(group_services.remove_responsable_impression(group_member), 1)

        member_role_model.objects.filter.assert_called_once_with(
            group_member=group_member,
            role=role,
        )

    @patch("app_group.services.GroupMemberFunction")
    def test_group_functions_require_same_group_but_accept_am_members(
        self, member_function_model
    ):
        group = build_group(1)
        other_group = build_group(2)
        am_member = build_group_member(
            group=group, member_kind=group_models.MEMBER_KIND_AM
        )
        function = group_models.GroupFunction(group=group, name="Chantre")
        other_function = group_models.GroupFunction(group=other_group, name="Orgue")
        assignment = object()
        member_function_model.objects.get_or_create.return_value = (assignment, True)

        self.assertIs(
            group_services.assign_group_function(am_member, function), assignment
        )
        with self.assertRaises(ValidationError):
            group_services.assign_group_function(am_member, other_function)

    @patch("app_group.services.GroupMemberFunction")
    def test_remove_group_function_requires_same_group_and_deletes_assignment(
        self, member_function_model
    ):
        group = build_group(1)
        other_group = build_group(2)
        group_member = build_group_member(
            group=group, member_kind=group_models.MEMBER_KIND_AM
        )
        function = group_models.GroupFunction(group=group, name="Chantre")
        other_function = group_models.GroupFunction(group=other_group, name="Orgue")
        member_function_model.objects.filter.return_value.delete.return_value = (1, {})

        self.assertEqual(
            group_services.remove_group_function(group_member, function), 1
        )

        member_function_model.objects.filter.assert_called_once_with(
            group_member=group_member,
            function=function,
        )
        with self.assertRaises(ValidationError):
            group_services.remove_group_function(group_member, other_function)

    def test_group_parameter_save_helpers_call_clean_and_save(self):
        group = build_group()
        objects = [
            (
                group_services.save_group_function,
                group_models.GroupFunction(group=group, name="Chantre"),
            ),
            (
                group_services.save_am_member_title,
                group_models.AmMemberTitle(group=group, label="Ami"),
            ),
            (
                group_services.save_group_location,
                group_models.GroupLocation(group=group, name="Eglise"),
            ),
            (
                group_services.save_planning_state,
                group_models.PlanningState(
                    group=group,
                    name="Publie",
                    color="#009688",
                    kind=group_models.PlanningState.KIND_CUSTOM,
                ),
            ),
        ]

        for save_func, instance in objects:
            with self.subTest(save_func=save_func.__name__):
                instance.full_clean = Mock()
                instance.save = Mock()

                self.assertIs(save_func(instance), instance)

                instance.full_clean.assert_called_once()
                instance.save.assert_called_once()

    @patch("app_group.services.AccessRequest")
    @patch("app_group.services.Member")
    @patch("app_group.services.CommonGroupUser")
    def test_access_request_requires_common_membership_without_am_access(
        self,
        common_group_user,
        member_model,
        access_request_model,
    ):
        group = build_group(1)
        member = build_member()
        member_model.objects.get_or_create.return_value = (member, False)
        common_group_user.objects.filter.return_value.first.return_value = (
            SimpleNamespace(am_access=False)
        )
        request = object()
        access_request_model.objects.get_or_create.return_value = (request, True)

        self.assertIs(
            group_services.create_access_request(
                group,
                member,
                consent_version="v1",
            ),
            request,
        )
        member_model.objects.get_or_create.assert_called_once_with(mm_id=member.mm_id)
        _args, kwargs = access_request_model.objects.get_or_create.call_args
        self.assertIs(kwargs["member"], member)

        common_group_user.objects.filter.return_value.first.return_value = None
        with self.assertRaises(ValidationError):
            group_services.create_access_request(group, member, consent_version="v1")

        common_group_user.objects.filter.return_value.first.return_value = (
            SimpleNamespace(am_access=True)
        )
        with self.assertRaises(ValidationError):
            group_services.create_access_request(group, member, consent_version="v1")

    @patch("app_group.services.CommonGroupJoinRequest")
    @patch("app_group.services.CommonGroupUser")
    @patch("app_group.services.Group")
    def test_common_join_request_requires_active_group_and_no_existing_membership(
        self,
        group_model,
        common_group_user,
        join_request_model,
    ):
        group_model.objects.filter.return_value.exists.return_value = False

        with self.assertRaises(ValidationError):
            group_services.create_common_join_request(
                7,
                "11111111-1111-1111-1111-111111111111",
            )

        group_model.objects.filter.return_value.exists.return_value = True
        common_group_user.objects.filter.return_value.exists.return_value = True
        with self.assertRaises(ValidationError):
            group_services.create_common_join_request(
                7,
                "11111111-1111-1111-1111-111111111111",
            )

        common_group_user.objects.filter.return_value.exists.return_value = False
        join_request = object()
        join_request_model.objects.get_or_create.return_value = (join_request, True)

        self.assertIs(
            group_services.create_common_join_request(
                7,
                "11111111-1111-1111-1111-111111111111",
            ),
            join_request,
        )

    @patch("app_group.services.GroupMember")
    @patch("app_group.services.Member")
    @patch("app_group.services.Group")
    @patch("app_group.services.transaction.atomic")
    @patch("app_group.services.CommonGroupUser")
    def test_accept_common_join_request_creates_membership_and_deletes_request(
        self,
        common_group_user,
        atomic,
        group_model,
        member_model,
        group_member_model,
    ):
        atomic.return_value.__enter__ = Mock(return_value=None)
        atomic.return_value.__exit__ = Mock(return_value=False)
        membership = Mock(am_access=False)
        common_group_user.objects.get_or_create.return_value = (membership, True)
        group = group_models.Group(gg_id=7)
        group_model.objects.get.return_value = group
        member = build_member()
        member_model.objects.get_or_create.return_value = (member, True)
        join_request = Mock(
            group_id=7,
            member_id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
        )

        self.assertIs(
            group_services.accept_common_join_request(join_request), membership
        )

        common_group_user.objects.get_or_create.assert_called_once_with(
            group_id=7,
            member_id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
            defaults={"is_group_admin": False, "am_access": True},
        )
        membership.save.assert_called_once_with(update_fields=["am_access"])
        group_model.objects.get.assert_called_once_with(pk=7)
        member_model.objects.get_or_create.assert_called_once_with(
            mm_id=uuid.UUID("11111111-1111-1111-1111-111111111111")
        )
        group_member_model.objects.get_or_create.assert_called_once()
        _args, kwargs = group_member_model.objects.get_or_create.call_args
        self.assertIs(kwargs["group"], group)
        self.assertIs(kwargs["member"], member)
        self.assertEqual(kwargs["member_kind"], group_models.MEMBER_KIND_ACCOUNT)
        join_request.delete.assert_called_once()

    def test_refuse_common_join_request_deletes_request(self):
        join_request = Mock()

        group_services.refuse_common_join_request(join_request)

        join_request.delete.assert_called_once()

    @patch("app_group.services.transaction.atomic")
    @patch("app_group.services.GroupMember")
    @patch("app_group.services.CommonGroupUser")
    def test_accept_access_request_enables_am_access_and_deletes_request(
        self,
        common_group_user,
        group_member_model,
        atomic,
    ):
        atomic.return_value.__enter__ = Mock(return_value=None)
        atomic.return_value.__exit__ = Mock(return_value=False)
        group = build_group(1)
        member = build_member()
        membership = Mock()
        common_group_user.objects.select_for_update.return_value.filter.return_value.first.return_value = membership
        group_member = build_group_member(group=group, member=member)
        group_member_model.objects.get_or_create.return_value = (group_member, True)
        access_request = Mock(
            group_id=1, member_id=member.mm_id, group=group, member=member
        )

        self.assertIs(
            group_services.accept_access_request(access_request), group_member
        )

        self.assertTrue(membership.am_access)
        membership.save.assert_called_once_with(update_fields=["am_access"])
        access_request.delete.assert_called_once()

    @patch("app_group.services.transaction.atomic")
    @patch("app_group.services.CommonGroupUser")
    def test_accept_access_request_requires_existing_common_membership(
        self,
        common_group_user,
        atomic,
    ):
        atomic.return_value.__enter__ = Mock(return_value=None)
        atomic.return_value.__exit__ = Mock(return_value=False)
        common_group_user.objects.select_for_update.return_value.filter.return_value.first.return_value = None
        group = build_group(1)
        access_request = Mock(
            group_id=1,
            member_id=build_member().mm_id,
            group=group,
            member=build_member(),
        )

        with self.assertRaises(ValidationError):
            group_services.accept_access_request(access_request)

    def test_refuse_access_request_deletes_request(self):
        access_request = Mock()

        group_services.refuse_access_request(access_request)

        access_request.delete.assert_called_once()

    @patch("app_group.services.is_common_group_responsable", return_value=True)
    @patch("app_group.services.AmMemberRequest")
    def test_am_member_request_hashes_token_and_requires_responsable(
        self,
        request_model,
        _is_responsable,
    ):
        group = build_group(1)
        requested_by = build_group_member(group=group, member=build_member())
        request = object()
        request_model.objects.create.return_value = request

        self.assertIs(
            group_services.create_am_member_request(
                group,
                requested_by,
                first_name="Alice",
                last_name="Doe",
                email="alice@example.test",
                consent_token="token-123",
                consent_version="v1",
            ),
            request,
        )

        create_kwargs = request_model.objects.create.call_args.kwargs
        self.assertNotEqual(create_kwargs["consent_token_hash"], "token-123")
        self.assertEqual(create_kwargs["email"], "alice@example.test")

    @patch("app_group.services.is_common_group_responsable", return_value=True)
    @patch("app_group.services.AmMemberRequest")
    def test_am_member_request_validates_identity_email_and_consent_version(
        self,
        request_model,
        _is_responsable,
    ):
        group = build_group(1)
        requested_by = build_group_member(group=group, member=build_member())

        invalid_payloads = [
            {
                "first_name": "",
                "last_name": "Doe",
                "email": "alice@example.test",
                "consent_version": "v1",
            },
            {
                "first_name": "Alice",
                "last_name": "",
                "email": "alice@example.test",
                "consent_version": "v1",
            },
            {
                "first_name": "Alice",
                "last_name": "Doe",
                "email": "",
                "consent_version": "v1",
            },
            {
                "first_name": "Alice",
                "last_name": "Doe",
                "email": "bad-email",
                "consent_version": "v1",
            },
            {
                "first_name": "Alice",
                "last_name": "Doe",
                "email": "alice@example.test",
                "consent_version": "",
            },
        ]

        for payload in invalid_payloads:
            with (
                self.subTest(payload=payload),
                self.assertRaises(ValidationError),
            ):
                group_services.create_am_member_request(
                    group,
                    requested_by,
                    consent_token="token-123",
                    **payload,
                )

        request_model.objects.create.assert_not_called()

    @patch("app_group.services.is_common_group_responsable", return_value=True)
    @patch("app_group.services.AmMemberRequest")
    def test_am_member_request_expiration_cannot_exceed_14_days(
        self,
        request_model,
        _is_responsable,
    ):
        now = timezone.now()
        group = build_group(1)
        requested_by = build_group_member(group=group, member=build_member())

        with self.assertRaises(ValidationError):
            group_services.create_am_member_request(
                group,
                requested_by,
                first_name="Alice",
                last_name="Doe",
                email="alice@example.test",
                consent_token="token-123",
                consent_version="v1",
                expires_at=now + timezone.timedelta(days=15),
                now=now,
            )

        with self.assertRaises(ValidationError):
            group_services.create_am_member_request(
                group,
                requested_by,
                first_name="Alice",
                last_name="Doe",
                email="alice@example.test",
                consent_token="token-123",
                consent_version="v1",
                expires_at=now,
                now=now,
            )

        request = object()
        request_model.objects.create.return_value = request
        self.assertIs(
            group_services.create_am_member_request(
                group,
                requested_by,
                first_name="Alice",
                last_name="Doe",
                email="alice@example.test",
                consent_token="token-123",
                consent_version="v1",
                expires_at=now + timezone.timedelta(days=14),
                now=now,
            ),
            request,
        )

    @patch("app_group.services.is_common_group_responsable", return_value=False)
    def test_am_member_request_requires_requester_to_be_responsable(
        self, _is_responsable
    ):
        group = build_group(1)
        requested_by = build_group_member(group=group, member=build_member())

        with self.assertRaises(PermissionDenied):
            group_services.create_am_member_request(
                group,
                requested_by,
                first_name="Alice",
                last_name="Doe",
                email="alice@example.test",
                consent_token="token-123",
                consent_version="v1",
            )

    @patch("app_group.services.is_common_group_responsable", return_value=True)
    def test_am_member_request_requires_same_group_and_account_requester(
        self, _is_responsable
    ):
        group = build_group(1)
        other_group = build_group(2)
        account_in_other_group = build_group_member(
            group=other_group, member=build_member()
        )
        am_requester = build_group_member(
            group=group, member_kind=group_models.MEMBER_KIND_AM
        )

        with self.assertRaises(ValidationError):
            group_services.create_am_member_request(
                group,
                account_in_other_group,
                first_name="Alice",
                last_name="Doe",
                email="alice@example.test",
                consent_token="token-123",
                consent_version="v1",
            )

        with self.assertRaises(ValidationError):
            group_services.create_am_member_request(
                group,
                am_requester,
                first_name="Alice",
                last_name="Doe",
                email="alice@example.test",
                consent_token="token-123",
                consent_version="v1",
            )

    def test_expire_and_refuse_am_member_request_purge_identifying_data(self):
        now = timezone.now()
        request = Mock(
            status=group_models.AmMemberRequest.STATUS_PENDING,
            expires_at=now,
            first_name="Alice",
            last_name="Doe",
            email="alice@example.test",
        )

        self.assertTrue(group_services.expire_am_member_request(request, now=now))
        self.assertEqual(request.status, group_models.AmMemberRequest.STATUS_EXPIRED)
        self.assertEqual(request.first_name, "")
        self.assertEqual(request.last_name, "")
        self.assertEqual(request.email, "")
        self.assertNotEqual(request.consent_token_hash, "alice@example.test")
        request.save.assert_called_once()

        refused = Mock(
            status=group_models.AmMemberRequest.STATUS_PENDING,
            first_name="Bob",
            last_name="Smith",
            email="bob@example.test",
        )
        group_services.refuse_am_member_request(refused, now=now)
        self.assertEqual(refused.status, group_models.AmMemberRequest.STATUS_REFUSED)
        self.assertEqual(refused.email, "")
        self.assertGreater(refused.purge_at, now)

    def test_expire_am_member_request_ignores_non_expired_or_non_pending_requests(self):
        now = timezone.now()
        pending_future = Mock(
            status=group_models.AmMemberRequest.STATUS_PENDING,
            expires_at=now + timezone.timedelta(days=1),
        )
        refused_expired = Mock(
            status=group_models.AmMemberRequest.STATUS_REFUSED,
            expires_at=now - timezone.timedelta(days=1),
        )

        self.assertFalse(
            group_services.expire_am_member_request(pending_future, now=now)
        )
        self.assertFalse(
            group_services.expire_am_member_request(refused_expired, now=now)
        )

        pending_future.save.assert_not_called()
        refused_expired.save.assert_not_called()

    @patch("app_group.services.assign_group_function")
    @patch("app_group.services.AmMember")
    @patch("app_group.services.GroupMember")
    @patch("app_group.services.transaction.atomic")
    def test_accept_am_member_request_creates_anchor_profile_and_functions(
        self,
        atomic,
        group_member_model,
        am_member_model,
        assign_function,
    ):
        atomic.return_value.__enter__ = Mock(return_value=None)
        atomic.return_value.__exit__ = Mock(return_value=False)
        now = timezone.now()
        group = build_group(1)
        group_member = build_group_member(
            group=group, member_kind=group_models.MEMBER_KIND_AM
        )
        function = group_models.GroupFunction(group=group, name="Chantre")
        am_member = object()
        request = Mock(
            status=group_models.AmMemberRequest.STATUS_PENDING,
            expires_at=now + timezone.timedelta(days=1),
            consent_token_hash=group_services.hash_personal_secret("token-123"),
            group=group,
            first_name="Alice",
            last_name="Doe",
            email="alice@example.test",
            consent_version="v1",
        )
        group_member_model.objects.create.return_value = group_member
        am_member_model.objects.create.return_value = am_member

        self.assertIs(
            group_services.accept_am_member_request(
                request,
                consent_token="token-123",
                withdrawal_secret="withdraw-me",
                functions=[function],
                now=now,
            ),
            am_member,
        )

        profile_kwargs = am_member_model.objects.create.call_args.kwargs
        self.assertNotEqual(profile_kwargs["withdrawal_secret_hash"], "withdraw-me")
        self.assertNotEqual(
            profile_kwargs["consent_email_fingerprint"],
            "alice@example.test",
        )
        assign_function.assert_called_once_with(group_member, function)
        request.delete.assert_called_once()

    def test_accept_am_member_request_rejects_title_from_another_group(self):
        now = timezone.now()
        group = build_group(1)
        other_group = build_group(2)
        title = group_models.AmMemberTitle(group=other_group, label="Ami")
        request = Mock(
            status=group_models.AmMemberRequest.STATUS_PENDING,
            expires_at=now + timezone.timedelta(days=1),
            consent_token_hash=group_services.hash_personal_secret("token-123"),
            group=group,
            group_id=group.gg_id,
        )

        with self.assertRaises(ValidationError):
            group_services.accept_am_member_request(
                request,
                consent_token="token-123",
                withdrawal_secret="withdraw-me",
                title=title,
                now=now,
            )

    def test_accept_am_member_request_rejects_bad_status_expiration_and_token(self):
        now = timezone.now()
        refused = Mock(
            status=group_models.AmMemberRequest.STATUS_REFUSED,
            expires_at=now + timezone.timedelta(days=1),
        )
        expired = Mock(
            status=group_models.AmMemberRequest.STATUS_PENDING,
            expires_at=now,
            first_name="Alice",
            last_name="Doe",
            email="alice@example.test",
            save=Mock(),
        )
        invalid_token = Mock(
            status=group_models.AmMemberRequest.STATUS_PENDING,
            expires_at=now + timezone.timedelta(days=1),
            consent_token_hash=group_services.hash_personal_secret("token-123"),
        )

        for request in [refused, expired, invalid_token]:
            with (
                self.subTest(request=request),
                self.assertRaises(ValidationError),
            ):
                group_services.accept_am_member_request(
                    request,
                    consent_token="bad-token",
                    withdrawal_secret="withdraw-me",
                    now=now,
                )

        expired.save.assert_called_once()

    @patch("app_group.services.SongTagVerse")
    @patch("app_group.services.Verse")
    @patch("app_group.services.SongTag")
    def test_tag_song_requires_group_match_and_initializes_verse_defaults(
        self,
        song_tag_model,
        verse_model,
        song_tag_verse_model,
    ):
        group = build_group(1)
        song = group_models.Song(group=group, song_id=12)
        tag = group_models.CommonGroupTag(gt_id=5, group_id=1, name="Entree")
        verse_1 = group_models.Verse(song=song, verse_id=1)
        verse_2 = group_models.Verse(song=song, verse_id=2)
        song_tag = group_models.SongTag(song=song, group_tag=tag)
        song_tag_model.objects.get_or_create.return_value = (song_tag, True)
        verse_model.objects.filter.return_value = [verse_1, verse_2]

        self.assertIs(group_services.tag_song(song, tag), song_tag)
        self.assertEqual(song_tag_verse_model.objects.get_or_create.call_count, 2)

        other_tag = group_models.CommonGroupTag(gt_id=6, group_id=2, name="Sortie")
        with self.assertRaises(ValidationError):
            group_services.tag_song(song, other_tag)

    @patch("app_group.services.Verse")
    @patch("app_group.services.Song")
    def test_add_song_to_repertoire_initializes_requested_verses(
        self, song_model, verse_model
    ):
        group = build_group(1)
        song = group_models.Song(group=group, song_id=12)
        song_model.objects.get_or_create.return_value = (song, True)

        self.assertIs(
            group_services.add_song_to_repertoire(
                group,
                song_id=12,
                verse_ids=[1, 2],
            ),
            song,
        )

        song_model.objects.get_or_create.assert_called_once_with(
            group=group,
            song_id=12,
        )
        self.assertEqual(verse_model.objects.get_or_create.call_count, 2)

    @patch("app_group.services.SongTagVerse")
    def test_tag_verse_selection_requires_same_song(self, song_tag_verse_model):
        group = build_group(1)
        song = group_models.Song(ss_id=10, group=group, song_id=12)
        other_song = group_models.Song(ss_id=11, group=group, song_id=13)
        tag = group_models.CommonGroupTag(gt_id=5, group_id=1, name="Entree")
        song_tag = group_models.SongTag(song=song, group_tag=tag)
        verse = group_models.Verse(song=song, verse_id=1)
        other_verse = group_models.Verse(song=other_song, verse_id=1)
        selection = object()
        song_tag_verse_model.objects.update_or_create.return_value = (selection, True)

        self.assertIs(
            group_services.set_tag_verse_selection(
                song_tag,
                verse,
                selected_by_default=False,
            ),
            selection,
        )
        with self.assertRaises(ValidationError):
            group_services.set_tag_verse_selection(
                song_tag,
                other_verse,
                selected_by_default=True,
            )

    def test_special_date_rule_field_validation(self):
        annual = group_models.SpecialDateRule(
            group=build_group(),
            name="Noel",
            rule_type=group_models.SpecialDateRule.RULE_ANNUAL_FIXED,
            collision_mode=group_models.SpecialDateRule.COLLISION_ADD,
            month=12,
            day=25,
        )
        group_services.validate_special_date_rule_fields(annual)

        invalid = group_models.SpecialDateRule(
            group=build_group(),
            name="Date",
            rule_type=group_models.SpecialDateRule.RULE_ONE_OFF,
            collision_mode=group_models.SpecialDateRule.COLLISION_ADD,
        )
        with self.assertRaises(ValidationError):
            group_services.validate_special_date_rule_fields(invalid)

    def test_celebration_rule_services_validate_parent_and_location_groups(self):
        group = build_group(1)
        other_group = build_group(2)
        location = group_models.GroupLocation(group=group, name="Eglise")
        other_location = group_models.GroupLocation(group=other_group, name="Chapelle")
        parent = group_models.CelebrationRule(
            group=other_group,
            weekday=7,
            time=time(10, 30),
            location=other_location,
        )
        rule = group_models.CelebrationRule(
            group=group,
            parent=parent,
            weekday=7,
            time=time(10, 30),
            location=location,
        )

        with self.assertRaises(ValidationError):
            group_services.save_celebration_rule(rule)

        rule.parent = None
        rule.location = other_location
        with self.assertRaises(ValidationError):
            group_services.save_celebration_rule(rule)

        rule.location = location
        rule.full_clean = Mock()
        rule.save = Mock()
        self.assertIs(group_services.save_celebration_rule(rule), rule)
        rule.full_clean.assert_called_once()
        rule.save.assert_called_once()

    def test_special_date_rule_service_validates_type_contract_before_save(self):
        group = build_group()
        valid = group_models.SpecialDateRule(
            group=group,
            name="Noel",
            rule_type=group_models.SpecialDateRule.RULE_ANNUAL_FIXED,
            collision_mode=group_models.SpecialDateRule.COLLISION_ADD,
            month=12,
            day=25,
        )
        valid.full_clean = Mock()
        valid.save = Mock()

        self.assertIs(group_services.save_special_date_rule(valid), valid)
        valid.full_clean.assert_called_once()
        valid.save.assert_called_once()

        invalid = group_models.SpecialDateRule(
            group=group,
            name="Fete",
            rule_type=group_models.SpecialDateRule.RULE_NTH_WEEKDAY,
            collision_mode=group_models.SpecialDateRule.COLLISION_ADD,
            month=5,
        )
        with self.assertRaises(ValidationError):
            group_services.save_special_date_rule(invalid)

        missing_annual_fields = group_models.SpecialDateRule(
            group=group,
            name="Noel",
            rule_type=group_models.SpecialDateRule.RULE_ANNUAL_FIXED,
            collision_mode=group_models.SpecialDateRule.COLLISION_ADD,
            month=12,
        )
        missing_one_off_date = group_models.SpecialDateRule(
            group=group,
            name="Ponctuelle",
            rule_type=group_models.SpecialDateRule.RULE_ONE_OFF,
            collision_mode=group_models.SpecialDateRule.COLLISION_ADD,
        )
        unsupported = group_models.SpecialDateRule(
            group=group,
            name="Autre",
            rule_type="unsupported",
            collision_mode=group_models.SpecialDateRule.COLLISION_ADD,
        )

        for rule in [missing_annual_fields, missing_one_off_date, unsupported]:
            with (
                self.subTest(rule=rule.name),
                self.assertRaises(ValidationError),
            ):
                group_services.save_special_date_rule(rule)

    @patch("app_group.services.save_celebration_rule")
    def test_create_celebration_rule_builds_rule_before_save(self, save_rule):
        group = build_group(1)
        location = group_models.GroupLocation(group=group, name="Eglise")
        save_rule.side_effect = lambda rule: rule

        rule = group_services.create_celebration_rule(
            group,
            weekday=7,
            time=time(10, 30),
            location=location,
            position=3,
            is_active=False,
        )

        self.assertEqual(rule.group, group)
        self.assertEqual(rule.weekday, 7)
        self.assertEqual(rule.time, time(10, 30))
        self.assertEqual(rule.location, location)
        self.assertEqual(rule.position, 3)
        self.assertFalse(rule.is_active)
        save_rule.assert_called_once_with(rule)

    @patch("app_group.services.save_special_date_rule")
    def test_create_special_date_rule_builds_rule_before_save(self, save_rule):
        group = build_group(1)
        save_rule.side_effect = lambda rule: rule

        rule = group_services.create_special_date_rule(
            group,
            name="Noel",
            rule_type=group_models.SpecialDateRule.RULE_ANNUAL_FIXED,
            collision_mode=group_models.SpecialDateRule.COLLISION_ADD,
            month=12,
            day=25,
            is_active=False,
        )

        self.assertEqual(rule.group, group)
        self.assertEqual(rule.name, "Noel")
        self.assertEqual(rule.rule_type, group_models.SpecialDateRule.RULE_ANNUAL_FIXED)
        self.assertEqual(rule.month, 12)
        self.assertEqual(rule.day, 25)
        self.assertFalse(rule.is_active)
        save_rule.assert_called_once_with(rule)

    def test_special_date_celebration_service_validates_rule_and_location(self):
        group = build_group(1)
        other_group = build_group(2)
        location = group_models.GroupLocation(group=group, name="Eglise")
        other_location = group_models.GroupLocation(group=other_group, name="Chapelle")
        rule = group_models.SpecialDateRule(
            group=group,
            name="Noel",
            rule_type=group_models.SpecialDateRule.RULE_ANNUAL_FIXED,
            collision_mode=group_models.SpecialDateRule.COLLISION_ADD,
            month=12,
            day=25,
        )
        other_rule = group_models.SpecialDateRule(
            group=group,
            name="Paques",
            rule_type=group_models.SpecialDateRule.RULE_ONE_OFF,
            collision_mode=group_models.SpecialDateRule.COLLISION_ADD,
            exact_date=timezone.localdate(),
        )
        parent = group_models.SpecialDateCelebration(
            special_date_rule=other_rule,
            time=time(10, 30),
            location=location,
        )
        celebration = group_models.SpecialDateCelebration(
            special_date_rule=rule,
            parent=parent,
            time=time(10, 30),
            location=location,
        )

        with self.assertRaises(ValidationError):
            group_services.save_special_date_celebration(celebration)

        celebration.parent = None
        celebration.location = other_location
        with self.assertRaises(ValidationError):
            group_services.save_special_date_celebration(celebration)

        celebration.location = location
        celebration.full_clean = Mock()
        celebration.save = Mock()
        self.assertIs(
            group_services.save_special_date_celebration(celebration),
            celebration,
        )
        celebration.full_clean.assert_called_once()
        celebration.save.assert_called_once()

    def test_special_date_celebration_parent_validation_uses_saved_rule_ids(self):
        parent = Mock(special_date_rule_id=2)
        celebration = Mock(special_date_rule_id=1, parent=parent)

        with self.assertRaises(ValidationError):
            group_services.validate_special_date_celebration_parent_rule(celebration)

    @patch("app_group.services.save_special_date_celebration")
    def test_create_special_date_celebration_builds_celebration_before_save(
        self, save_celebration
    ):
        group = build_group(1)
        location = group_models.GroupLocation(group=group, name="Eglise")
        rule = group_models.SpecialDateRule(
            group=group,
            name="Noel",
            rule_type=group_models.SpecialDateRule.RULE_ANNUAL_FIXED,
            collision_mode=group_models.SpecialDateRule.COLLISION_ADD,
            month=12,
            day=25,
        )
        save_celebration.side_effect = lambda celebration: celebration

        celebration = group_services.create_special_date_celebration(
            rule,
            time=time(10, 30),
            location=location,
            position=2,
        )

        self.assertEqual(celebration.special_date_rule, rule)
        self.assertEqual(celebration.time, time(10, 30))
        self.assertEqual(celebration.location, location)
        self.assertEqual(celebration.position, 2)
        save_celebration.assert_called_once_with(celebration)


class AppGroupMigrationContractTests(SimpleTestCase):
    def test_initial_migration_does_not_create_managed_common_tables(self):
        common_create_models = [
            operation
            for operation in initial_migration.Migration.operations
            if isinstance(operation, migrations.CreateModel)
            and operation.options.get("db_table", "").startswith('common"')
        ]

        self.assertTrue(common_create_models)
        for operation in common_create_models:
            with self.subTest(model=operation.name):
                self.assertFalse(operation.options.get("managed", True))

    def test_initial_migration_creates_only_managed_am_tables(self):
        managed_create_tables = [
            operation.options.get("db_table")
            for operation in initial_migration.Migration.operations
            if isinstance(operation, migrations.CreateModel)
            and operation.options.get("managed", True)
        ]

        self.assertTrue(managed_create_tables)
        self.assertTrue(
            all(table.startswith('am"') for table in managed_create_tables),
            managed_create_tables,
        )

    def test_initial_migration_contains_cross_schema_foreign_keys(self):
        run_sql = "\n".join(
            operation.sql
            for operation in initial_migration.Migration.operations
            if isinstance(operation, migrations.RunSQL)
        )

        expected_fragments = [
            'REFERENCES "common"."g_groups" ("group_id")',
            'REFERENCES "common"."g_group_user" ("group_id", "member_id")',
            'REFERENCES "lss"."s_songs" ("song_id")',
            'REFERENCES "lss"."s_verses" ("verse_id")',
        ]

        for fragment in expected_fragments:
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, run_sql)

    def test_initial_migration_does_not_require_common_group_tags_yet(self):
        run_sql = "\n".join(
            operation.sql
            for operation in initial_migration.Migration.operations
            if isinstance(operation, migrations.RunSQL)
        )

        self.assertNotIn('REFERENCES "common"."group_tags"', run_sql)

    def test_second_migration_adds_common_group_tags_foreign_key(self):
        operation = second_migration.Migration.operations[0]
        self.assertIsInstance(operation, migrations.SeparateDatabaseAndState)

        run_sql = "\n".join(
            database_operation.sql
            for database_operation in operation.database_operations
            if isinstance(database_operation, migrations.RunSQL)
        )

        self.assertIn(
            'REFERENCES "common"."group_tags" ("gt_id")',
            run_sql,
        )

    def test_third_migration_updates_common_group_tag_state_only(self):
        operation = third_migration.Migration.operations[0]

        self.assertIsInstance(operation, migrations.SeparateDatabaseAndState)
        self.assertEqual(operation.database_operations, [])
        self.assertEqual(
            [state_operation.name for state_operation in operation.state_operations],
            ["sort_order", "is_active"],
        )

    def test_fourth_migration_adds_contract_constraints(self):
        constraint_names = [
            operation.constraint.name
            for operation in fourth_migration.Migration.operations
            if isinstance(operation, migrations.AddConstraint)
        ]

        self.assertEqual(
            constraint_names,
            [
                "g_celebration_rule_weekday_valid",
                "g_celebration_rule_active_slot_unique",
                "g_special_date_rule_month_valid",
                "g_special_date_rule_day_valid",
                "g_special_date_rule_weekday_valid",
            ],
        )
