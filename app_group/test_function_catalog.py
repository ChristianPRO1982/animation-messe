import json
from types import SimpleNamespace
from unittest.mock import patch

from django.core.exceptions import PermissionDenied, ValidationError
from django.test import Client, RequestFactory, SimpleTestCase
from django.urls import reverse

from app_group import forms, models, services, views


class FunctionCatalogServiceTests(SimpleTestCase):
    def setUp(self):
        self.group = models.Group(gg_id=7)
        self.groups = self.enterContext(patch.object(models.Group, "objects"))
        self.functions = self.enterContext(
            patch.object(models.GroupFunction, "objects")
        )
        self.atomic = self.enterContext(patch("app_group.services.transaction.atomic"))
        self.clean = self.enterContext(patch.object(models.GroupFunction, "full_clean"))
        self.save = self.enterContext(patch.object(models.GroupFunction, "save"))
        self.first = models.GroupFunction(
            gf_id=1, group=self.group, name="Chantre", position=3
        )
        self.second = models.GroupFunction(
            gf_id=2, group=self.group, name="Organiste", position=9, is_active=False
        )

    def test_creation_appends_after_existing_positions_and_keeps_defaults(self):
        self.functions.filter.return_value.aggregate.return_value = {"last": 9}
        created = services.create_group_function(self.group, name="  Chœur  ")
        self.assertEqual((created.name, created.position), ("Chœur", 10))
        self.assertTrue(created.is_active)
        self.assertFalse(created.auto_edit_celebration)
        self.groups.select_for_update.return_value.get.assert_called_once_with(pk=7)
        self.clean.assert_called_once()
        self.save.assert_called_once()

    def test_first_function_starts_at_zero_and_accepts_explicit_flags(self):
        self.functions.filter.return_value.aggregate.return_value = {"last": None}
        created = services.create_group_function(
            self.group, name="Chantre", is_active=False, auto_edit_celebration=True
        )
        self.assertEqual(created.position, 0)
        self.assertFalse(created.is_active)
        self.assertTrue(created.auto_edit_celebration)

    def test_creation_preserves_model_validation_including_duplicate_names(self):
        self.functions.filter.return_value.aggregate.return_value = {"last": 0}
        self.clean.side_effect = ValidationError("Nom déjà utilisé")
        with self.assertRaisesMessage(ValidationError, "Nom déjà utilisé"):
            services.create_group_function(self.group, name=" chantre ")
        self.save.assert_not_called()
        self.assertIs(
            self.atomic.return_value.__exit__.call_args.args[0], ValidationError
        )

    def test_each_flag_is_saved_without_writing_the_other_fields(self):
        for field in ("is_active", "auto_edit_celebration"):
            with self.subTest(field=field):
                self.save.reset_mock()
                self.first.is_active = True
                self.first.auto_edit_celebration = False
                self.functions.get.return_value = self.first
                self.functions.filter.return_value.order_by.return_value = [
                    self.first,
                    self.second,
                ]
                result = services.update_group_function_flag(
                    self.group, function_id=1, field=field, value=field != "is_active"
                )
                self.functions.get.assert_called_with(group=self.group, pk=1)
                self.save.assert_called_once_with(update_fields=[field, "updated_at"])
                self.assertEqual(self.first.name, "Chantre")
                self.assertEqual(self.first.position, 3)
                self.assertEqual(result, [self.first, self.second])
                self.assertFalse(
                    self.first.is_active
                    if field == "is_active"
                    else not self.first.auto_edit_celebration
                )

    def test_flag_rejects_unknown_fields_and_non_boolean_values(self):
        for field, value in (
            ("name", True),
            ("position", True),
            ("is_active", "false"),
            ("is_active", 1),
        ):
            with (
                self.subTest(field=field, value=value),
                self.assertRaises(ValidationError),
            ):
                services.update_group_function_flag(
                    self.group, function_id=1, field=field, value=value
                )
        self.functions.get.assert_not_called()

    def test_function_from_another_group_or_missing_is_rejected(self):
        self.functions.get.side_effect = models.GroupFunction.DoesNotExist
        with self.assertRaisesMessage(ValidationError, "dans ce groupe"):
            services.update_group_function_flag(
                self.group, function_id=10, field="is_active", value=False
            )
        self.functions.get.assert_called_once_with(group=self.group, pk=10)
        self.save.assert_not_called()

    def test_reorder_includes_inactive_functions_and_preserves_flags_and_identity(self):
        self.functions.filter.return_value = [self.first, self.second]
        result = services.reorder_group_functions(self.group, [2, 1])
        self.assertEqual(result, [self.second, self.first])
        self.assertEqual((self.second.position, self.first.position), (0, 1))
        self.assertFalse(self.second.is_active)
        self.assertEqual((self.first.pk, self.second.pk), (1, 2))
        self.functions.bulk_update.assert_called_once_with(
            result, ["position", "updated_at"]
        )
        self.groups.select_for_update.return_value.get.assert_called_once_with(pk=7)
        self.save.assert_not_called()

    def test_reorder_rejects_incomplete_duplicate_foreign_and_invalid_ids(self):
        self.functions.filter.return_value = [self.first, self.second]
        for ids in ([1], [1, 1], [1, 8], [], [True, 2], ["1", 2], [0, 2]):
            with self.subTest(ids=ids), self.assertRaises(ValidationError):
                services.reorder_group_functions(self.group, ids)
        self.functions.bulk_update.assert_not_called()
        self.assertEqual((self.first.position, self.second.position), (3, 9))

    def test_no_assignment_model_is_written_by_catalog_changes(self):
        with patch.object(models.GroupMemberFunction, "objects") as assignments:
            self.functions.get.return_value = self.first
            self.functions.filter.return_value.order_by.return_value = [self.first]
            services.update_group_function_flag(
                self.group, function_id=1, field="is_active", value=False
            )
            self.functions.filter.return_value = [self.first]
            services.reorder_group_functions(self.group, [1])
        self.assertEqual(assignments.mock_calls, [])


class FunctionCatalogViewTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.group = models.Group(gg_id=7)
        self.common = SimpleNamespace(group_id=7, name="Chorale", status="open")
        self.user = SimpleNamespace(is_authenticated=True, is_admin=False)
        self.enterContext(
            patch("app_group.views._get_common_group", return_value=self.common)
        )
        group_objects = self.enterContext(patch.object(models.Group, "objects"))
        group_objects.filter.return_value.first.return_value = self.group
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
        self.context = self.enterContext(
            patch(
                "app_group.views._build_group_context",
                return_value={"common_group": self.common, "functions": []},
            )
        )
        self.function = models.GroupFunction(
            gf_id=1, group=self.group, name="Chantre", position=0
        )

    def request(self, data=None, authenticated=True):
        request = (
            self.factory.get("/groups/7/functions/")
            if data is None
            else self.factory.post("/groups/7/functions/", data)
        )
        request.user = (
            self.user if authenticated else SimpleNamespace(is_authenticated=False)
        )
        request.session = {}
        return request

    def test_creation_calls_service_and_redirects_ignoring_position_and_object_id(self):
        with patch("app_group.views.services.create_group_function") as create:
            response = views.group_functions(
                self.request(
                    {
                        "action": "create_function",
                        "name": "Organiste",
                        "is_active": "on",
                        "object_id": "1",
                        "position": "0",
                    }
                ),
                7,
            )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("group_functions", args=[7]))
        create.assert_called_once_with(
            self.group, name="Organiste", is_active=True, auto_edit_celebration=False
        )

    def test_invalid_creation_keeps_input_and_errors_on_the_page(self):
        with patch(
            "app_group.views.services.create_group_function",
            side_effect=ValidationError("Nom déjà utilisé"),
        ):
            response = views.group_functions(
                self.request(
                    {"action": "create_function", "name": "Chantre", "is_active": "on"}
                ),
                7,
            )
        self.assertEqual(response.status_code, 400)
        self.assertContains(response, 'value="Chantre"', status_code=400)
        self.assertContains(response, "Nom déjà utilisé", status_code=400)
        with patch("app_group.views.services.create_group_function") as create:
            response = views.group_functions(
                self.request({"action": "create_function", "name": ""}), 7
            )
        self.assertEqual(response.status_code, 400)
        create.assert_not_called()

    def test_flag_and_reorder_return_canonical_state(self):
        for action, data, service_name, expected_kwargs in (
            (
                "update_function",
                {"function_id": "1", "field": "is_active", "value": "false"},
                "update_group_function_flag",
                {"function_id": 1, "field": "is_active", "value": False},
            ),
            (
                "reorder_functions",
                {"function_ids": "[1]"},
                "reorder_group_functions",
                None,
            ),
        ):
            with (
                self.subTest(action=action),
                patch(
                    f"app_group.views.services.{service_name}",
                    return_value=[self.function],
                ) as service,
            ):
                response = views.group_functions(
                    self.request({"action": action, **data}), 7
                )
                self.assertEqual(response.status_code, 200)
                self.assertEqual(
                    json.loads(response.content),
                    {
                        "functions": [
                            {
                                "id": 1,
                                "position": 0,
                                "is_active": True,
                                "auto_edit_celebration": False,
                            }
                        ]
                    },
                )
                if expected_kwargs:
                    service.assert_called_once_with(self.group, **expected_kwargs)
                else:
                    service.assert_called_once_with(self.group, [1])

    def test_invalid_payloads_and_service_validation_return_json_errors(self):
        for data in (
            {
                "action": "update_function",
                "function_id": "1",
                "field": "name",
                "value": "true",
            },
            {
                "action": "update_function",
                "function_id": "0",
                "field": "is_active",
                "value": "true",
            },
            {
                "action": "update_function",
                "function_id": "1",
                "field": "is_active",
                "value": "yes",
            },
            {"action": "reorder_functions", "function_ids": "not json"},
            {"action": "reorder_functions", "function_ids": "{}"},
            {"action": "reorder_functions", "function_ids": "[true]"},
            {"action": "reorder_functions", "function_ids": '["1"]'},
        ):
            with self.subTest(data=data):
                response = views.group_functions(self.request(data), 7)
                self.assertEqual(response.status_code, 400)
                self.assertIn("error", json.loads(response.content))
        with patch(
            "app_group.views.services.reorder_group_functions",
            side_effect=ValidationError("Rechargez la page"),
        ):
            response = views.group_functions(
                self.request({"action": "reorder_functions", "function_ids": "[1]"}), 7
            )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Rechargez", json.loads(response.content)["error"])

    def test_legacy_assign_remove_and_save_operations_are_rejected(self):
        with patch("app_group.views._dispatch_group_action") as dispatch:
            for action in (
                "assign_function",
                "remove_function",
                "save_function",
                "activate_group",
                "unknown",
            ):
                with self.subTest(action=action):
                    response = views.group_functions(
                        self.request({"action": action}), 7
                    )
                    self.assertEqual(response.status_code, 400)
        dispatch.assert_not_called()

    def test_permissions_apply_to_get_creation_and_ajax_for_both_manager_roles(self):
        for global_admin in (False, True):
            self.user.is_admin = global_admin
            response = views.group_functions(self.request(), 7)
            self.assertEqual(response.status_code, 200)
        self.access.return_value.can_manage_group = False
        for data in (
            None,
            {"action": "create_function"},
            {"action": "update_function"},
            {"action": "reorder_functions"},
        ):
            with self.subTest(data=data):
                response = views.group_functions(self.request(data), 7)
                self.assertEqual(response.status_code, 403)
        self.access.return_value.can_manage_group = True
        self.require.side_effect = PermissionDenied
        response = views.group_functions(
            self.request({"action": "reorder_functions", "function_ids": "[1]"}), 7
        )
        self.assertEqual(response.status_code, 403)

    def test_anonymous_ajax_and_inactive_group_are_handled(self):
        request = self.request({"action": "update_function"}, authenticated=False)
        response = views.group_functions(request, 7)
        self.assertEqual(response.status_code, 403)
        self.assertIn("error", json.loads(response.content))
        with patch.object(models.Group, "objects") as groups:
            groups.filter.return_value.first.return_value = None
            response = views.group_functions(
                self.request({"action": "reorder_functions"}), 7
            )
        self.assertEqual(response.status_code, 404)

    def test_management_ui_keeps_inactive_functions_without_assignment_or_position_fields(
        self,
    ):
        self.function.is_active = False
        self.context.return_value["functions"] = [self.function]
        response = views.group_functions(self.request(), 7)
        self.assertContains(response, "Chantre")
        self.assertContains(response, "⋮↕⋮")
        self.assertContains(response, 'data-function-field="auto_edit_celebration"')
        self.assertContains(response, 'name="action" value="create_function"')
        self.assertNotContains(response, 'name="position"')
        self.assertNotContains(response, "Affectations")
        self.assertNotContains(response, "assign_function")
        self.assertNotContains(response, "<table")

    def test_ajax_requires_csrf_token(self):
        response = Client(enforce_csrf_checks=True).post(
            reverse("group_functions", args=[7]),
            {"action": "reorder_functions", "function_ids": "[1]"},
        )
        self.assertEqual(response.status_code, 403)
        self.require.assert_not_called()

    def test_create_form_exposes_only_the_three_creation_fields(self):
        form = forms.GroupFunctionCreateForm(initial={"action": "create_function"})
        self.assertEqual(
            [field.name for field in form.visible_fields()],
            ["name", "is_active", "auto_edit_celebration"],
        )
        self.assertTrue(form["is_active"].value())
        self.assertFalse(bool(form["auto_edit_celebration"].value()))
