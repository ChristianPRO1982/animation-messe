import json
from types import SimpleNamespace
from unittest.mock import patch

from django.core.exceptions import PermissionDenied, ValidationError
from django.test import Client, RequestFactory, SimpleTestCase
from django.urls import reverse

from app_group import forms, models, services, views


class TitleCatalogServiceTests(SimpleTestCase):
    def setUp(self):
        self.group = models.Group(gg_id=7)
        self.groups = self.enterContext(patch.object(models.Group, "objects"))
        self.titles = self.enterContext(patch.object(models.AmMemberTitle, "objects"))
        self.atomic = self.enterContext(patch("app_group.services.transaction.atomic"))
        self.clean = self.enterContext(patch.object(models.AmMemberTitle, "full_clean"))
        self.save = self.enterContext(patch.object(models.AmMemberTitle, "save"))
        self.first = models.AmMemberTitle(
            gamt_id=1, group=self.group, label="Père", position=3
        )
        self.second = models.AmMemberTitle(
            gamt_id=2, group=self.group, label="Sœur", position=9, is_active=False
        )

    def test_creation_appends_after_all_titles_including_inactive(self):
        for last, expected in ((None, 0), (9, 10)):
            with self.subTest(last=last):
                self.titles.filter.return_value.aggregate.return_value = {"last": last}
                title = services.create_am_member_title(self.group, label="  Frère  ")
                self.assertEqual((title.label, title.position), ("Frère", expected))
                self.assertTrue(title.is_active)
                self.groups.select_for_update.return_value.get.assert_called_with(pk=7)
        self.assertEqual(self.clean.call_count, 2)
        self.assertEqual(self.save.call_count, 2)

    def test_creation_accepts_inactive_and_preserves_model_validation(self):
        self.titles.filter.return_value.aggregate.return_value = {"last": None}
        title = services.create_am_member_title(
            self.group, label="Diacre", is_active=False
        )
        self.assertFalse(title.is_active)
        self.save.reset_mock()
        self.clean.side_effect = ValidationError("Libellé invalide")
        with self.assertRaisesMessage(ValidationError, "Libellé invalide"):
            services.create_am_member_title(self.group, label="Diacre")
        self.save.assert_not_called()
        self.assertIs(
            self.atomic.return_value.__exit__.call_args.args[0], ValidationError
        )

    def test_activation_saves_only_active_flag_and_keeps_member_reference(self):
        member = models.AmMember(gam_id=4, title=self.first)
        self.titles.get.return_value = self.first
        self.titles.filter.return_value.order_by.return_value = [
            self.first,
            self.second,
        ]
        with patch.object(models.AmMember, "objects") as members:
            for value in (False, True):
                with self.subTest(value=value):
                    self.save.reset_mock()
                    result = services.update_am_member_title(
                        self.group, title_id=1, field="is_active", value=value
                    )
                    self.assertEqual(self.first.is_active, value)
                    self.assertEqual(
                        (self.first.label, self.first.position), ("Père", 3)
                    )
                    self.assertEqual(member.title_id, 1)
                    self.assertEqual(result, [self.first, self.second])
                    self.save.assert_called_once_with(update_fields=["is_active"])
                    self.titles.get.assert_called_with(group=self.group, pk=1)
            self.assertEqual(members.mock_calls, [])

    def test_unsupported_fields_values_and_foreign_titles_are_rejected(self):
        for field, value in (
            ("label", True),
            ("position", True),
            ("auto_edit_celebration", True),
            ("is_active", "false"),
            ("is_active", 0),
        ):
            with (
                self.subTest(field=field, value=value),
                self.assertRaises(ValidationError),
            ):
                services.update_am_member_title(
                    self.group, title_id=1, field=field, value=value
                )
        self.titles.get.assert_not_called()
        self.titles.get.side_effect = models.AmMemberTitle.DoesNotExist
        with self.assertRaisesMessage(ValidationError, "dans ce groupe"):
            services.update_am_member_title(
                self.group, title_id=8, field="is_active", value=False
            )
        self.titles.get.assert_called_once_with(group=self.group, pk=8)
        self.save.assert_not_called()

    def test_reordering_preserves_ids_activation_and_member_links(self):
        member = models.AmMember(gam_id=4, title=self.second)
        self.titles.filter.return_value = [self.first, self.second]
        with patch.object(models.AmMember, "objects") as members:
            result = services.reorder_am_member_titles(self.group, [2, 1])
            self.assertEqual(members.mock_calls, [])
        self.assertEqual(result, [self.second, self.first])
        self.assertEqual((self.second.position, self.first.position), (0, 1))
        self.assertEqual(member.title_id, 2)
        self.assertFalse(self.second.is_active)
        self.titles.bulk_update.assert_called_once_with(result, ["position"])
        self.groups.select_for_update.return_value.get.assert_called_once_with(pk=7)

    def test_incomplete_duplicate_foreign_and_invalid_orders_do_not_write(self):
        self.titles.filter.return_value = [self.first, self.second]
        for ids in ([1], [1, 1], [1, 8], [], [True, 2], ["1", 2], [0, 2]):
            with self.subTest(ids=ids), self.assertRaises(ValidationError):
                services.reorder_am_member_titles(self.group, ids)
        self.titles.bulk_update.assert_not_called()
        self.assertEqual((self.first.position, self.second.position), (3, 9))


class TitleCatalogViewTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.group = models.Group(gg_id=7)
        self.common = SimpleNamespace(group_id=7, name="Chorale", status="open")
        self.user = SimpleNamespace(is_authenticated=True, is_admin=False)
        self.enterContext(
            patch("app_group.views._get_common_group", return_value=self.common)
        )
        self.groups = self.enterContext(patch.object(models.Group, "objects"))
        self.groups.filter.return_value.first.return_value = self.group
        self.access = self.enterContext(
            patch(
                "app_group.views._build_group_access_context",
                return_value=SimpleNamespace(can_manage_group=True),
            )
        )
        self.require = self.enterContext(
            patch("app_group.views.services.require_group_manager")
        )
        self.enterContext(patch("app_group.views.messages"))
        self.title = models.AmMemberTitle(
            gamt_id=1, group=self.group, label="Père", position=0
        )
        self.enterContext(
            patch(
                "app_group.views._build_group_context",
                return_value={"common_group": self.common, "titles": [self.title]},
            )
        )

    def request(self, data=None, authenticated=True):
        request = (
            self.factory.get("/groups/7/am-member-titles/")
            if data is None
            else self.factory.post("/groups/7/am-member-titles/", data)
        )
        request.user = (
            self.user if authenticated else SimpleNamespace(is_authenticated=False)
        )
        request.session = {}
        return request

    def test_get_uses_shared_controller_and_creation_fields_without_position(self):
        self.title.is_active = False
        response = views.group_am_member_titles(self.request(), 7)
        for text in (
            "Gérer les titres Membre AM",
            "Père",
            "⋮↕⋮",
            "js/group_catalog.js",
            'data-catalog-field="is_active"',
            'name="action" value="create_am_member_title"',
        ):
            self.assertContains(response, text)
        self.assertNotContains(response, 'name="position"')
        self.assertNotContains(response, "auto_edit_celebration")
        self.assertNotContains(response, "<table")
        form = forms.AmMemberTitleCreateForm(
            initial={"action": "create_am_member_title"}
        )
        self.assertEqual(
            [field.name for field in form.visible_fields()], ["label", "is_active"]
        )
        self.assertTrue(form["is_active"].value())

    def test_creation_redirects_and_ignores_position_and_existing_id(self):
        with patch("app_group.views.services.create_am_member_title") as create:
            response = views.group_am_member_titles(
                self.request(
                    {
                        "action": "create_am_member_title",
                        "label": "Frère",
                        "is_active": "on",
                        "object_id": "1",
                        "position": "0",
                    }
                ),
                7,
            )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("group_am_member_titles", args=[7]))
        create.assert_called_once_with(self.group, label="Frère", is_active=True)

    def test_invalid_creation_keeps_label_and_errors(self):
        with patch(
            "app_group.views.services.create_am_member_title",
            side_effect=ValidationError("Libellé invalide"),
        ):
            response = views.group_am_member_titles(
                self.request({"action": "create_am_member_title", "label": "Frère"}), 7
            )
        self.assertContains(response, 'value="Frère"', status_code=400)
        self.assertContains(response, "Libellé invalide", status_code=400)
        with patch("app_group.views.services.create_am_member_title") as create:
            response = views.group_am_member_titles(
                self.request({"action": "create_am_member_title", "label": ""}), 7
            )
        self.assertEqual(response.status_code, 400)
        create.assert_not_called()

    def test_activation_and_order_return_titles_only_with_current_state(self):
        for action, payload, service_name, expected in (
            (
                "update_am_member_title",
                {"title_id": "1", "field": "is_active", "value": "false"},
                "update_am_member_title",
                {"title_id": 1, "field": "is_active", "value": False},
            ),
            (
                "reorder_am_member_titles",
                {"title_ids": "[1]"},
                "reorder_am_member_titles",
                None,
            ),
        ):
            with (
                self.subTest(action=action),
                patch(
                    f"app_group.views.services.{service_name}",
                    return_value=[self.title],
                ) as service,
            ):
                response = views.group_am_member_titles(
                    self.request({"action": action, **payload}), 7
                )
                self.assertEqual(response.status_code, 200)
                self.assertEqual(
                    json.loads(response.content),
                    {"titles": [{"id": 1, "position": 0, "is_active": True}]},
                )
                if expected:
                    service.assert_called_once_with(self.group, **expected)
                else:
                    service.assert_called_once_with(self.group, [1])

    def test_bad_payloads_and_legacy_or_cross_catalog_actions_are_rejected(self):
        for data in (
            {"action": "save_am_member_title", "object_id": "1", "label": "Autre"},
            {"action": "create_function", "name": "Chantre"},
            {
                "action": "update_am_member_title",
                "title_id": "0",
                "field": "is_active",
                "value": "true",
            },
            {
                "action": "update_am_member_title",
                "title_id": "1",
                "field": "label",
                "value": "true",
            },
            {
                "action": "update_am_member_title",
                "title_id": "1",
                "field": "auto_edit_celebration",
                "value": "true",
            },
            {
                "action": "update_am_member_title",
                "title_id": "1",
                "field": "is_active",
                "value": "on",
            },
            {"action": "reorder_am_member_titles", "title_ids": "not json"},
            {"action": "reorder_am_member_titles", "title_ids": "{}"},
            {"action": "reorder_am_member_titles", "title_ids": "[true]"},
            {"action": "reorder_am_member_titles", "title_ids": '["1"]'},
        ):
            with self.subTest(data=data):
                response = views.group_am_member_titles(self.request(data), 7)
                self.assertEqual(response.status_code, 400)
                self.assertIn("error", json.loads(response.content))
        with patch(
            "app_group.views.services.reorder_am_member_titles",
            side_effect=ValidationError("Rechargez la page"),
        ):
            response = views.group_am_member_titles(
                self.request(
                    {"action": "reorder_am_member_titles", "title_ids": "[1]"}
                ),
                7,
            )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Rechargez", json.loads(response.content)["error"])

    def test_permissions_for_get_create_and_ajax(self):
        for admin in (False, True):
            self.user.is_admin = admin
            self.assertEqual(
                views.group_am_member_titles(self.request(), 7).status_code, 200
            )
        self.access.return_value.can_manage_group = False
        for data in (
            None,
            {"action": "create_am_member_title"},
            {"action": "update_am_member_title"},
            {"action": "reorder_am_member_titles"},
        ):
            with self.subTest(data=data):
                self.assertEqual(
                    views.group_am_member_titles(self.request(data), 7).status_code, 403
                )
        self.access.return_value.can_manage_group = True
        self.require.side_effect = PermissionDenied
        response = views.group_am_member_titles(
            self.request({"action": "reorder_am_member_titles", "title_ids": "[1]"}), 7
        )
        self.assertEqual(response.status_code, 403)

    def test_expired_session_inactive_group_and_csrf_failures(self):
        response = views.group_am_member_titles(
            self.request({"action": "update_am_member_title"}, authenticated=False), 7
        )
        self.assertEqual(response.status_code, 403)
        self.assertIn("error", json.loads(response.content))
        self.groups.filter.return_value.first.return_value = None
        response = views.group_am_member_titles(
            self.request({"action": "reorder_am_member_titles"}), 7
        )
        self.assertEqual(response.status_code, 404)
        response = Client(enforce_csrf_checks=True).post(
            reverse("group_am_member_titles", args=[7]),
            {"action": "update_am_member_title"},
        )
        self.assertEqual(response.status_code, 403)
        self.require.assert_not_called()
