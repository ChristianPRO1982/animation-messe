import json
import uuid
from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.core.exceptions import ValidationError
from django.test import SimpleTestCase, override_settings

from app_main.models import SiteParams
from app_member import context_processors, services
from app_member.forms import SiteParamsAdminForm
from app_member.models import Member, MemberPreferences, validate_song_search
from app_member.services import (
    DirectoryMemberSearchResult,
    MemberRoleFlags,
    _normalize_uuid,
    _search_directory_users_with_sql,
    _user_table_has_column,
    _validate_identifier,
    can_manage_global_popup,
    can_manage_groups_globally,
    can_manage_site_members,
    can_manage_site_settings,
    get_member_role_flags,
    get_member_role_flags_safe,
    search_directory_members,
    set_member_role,
)


class MemberPreferencesTests(SimpleTestCase):
    def test_default_preferences_keep_member_ui_contract(self):
        member = Member(mm_id=uuid.UUID("11111111-1111-1111-1111-111111111111"))
        preferences = MemberPreferences(
            member=member,
        )

        self.assertEqual(preferences.theme_slug, "normal")
        self.assertEqual(preferences.calendar_week_start, "monday")

    def test_member_admin_flag_defaults_to_false(self):
        member = Member(mm_id=uuid.UUID("11111111-1111-1111-1111-111111111111"))
        self.assertFalse(member.is_admin)

    def test_legacy_song_search_validator_remains_available_for_migrations(self):
        valid_payload = {
            "text": "",
            "everywhere": False,
            "match_all_selected_refs": False,
            "genre_ids": [],
            "band_ids": [],
            "artist_ids": [],
            "validation": "all",
            "favorites_only": False,
        }

        validate_song_search(valid_payload)

        with self.assertRaisesMessage(ValidationError, "objet JSON"):
            validate_song_search([])
        with self.assertRaisesMessage(ValidationError, "validation"):
            validate_song_search({**valid_payload, "validation": "bad"})
        with self.assertRaisesMessage(ValidationError, "genre_ids"):
            validate_song_search({**valid_payload, "genre_ids": ["1"]})


class PermissionHelperTests(SimpleTestCase):
    def test_permission_helpers_follow_admin_role(self):
        admin_user = type(
            "User",
            (),
            {"is_authenticated": True, "is_admin": True},
        )()
        member_user = type(
            "User",
            (),
            {"is_authenticated": True, "is_admin": False},
        )()

        self.assertTrue(can_manage_site_members(admin_user))
        self.assertTrue(can_manage_site_settings(admin_user))
        self.assertTrue(can_manage_global_popup(admin_user))
        self.assertTrue(can_manage_groups_globally(admin_user))
        self.assertFalse(can_manage_site_members(member_user))
        self.assertFalse(can_manage_site_settings(member_user))


class MemberServiceTests(SimpleTestCase):
    databases = {"default"}

    def test_uuid_and_identifier_validation(self):
        self.assertEqual(
            _normalize_uuid("11111111-1111-1111-1111-111111111111"),
            "11111111-1111-1111-1111-111111111111",
        )
        self.assertEqual(_validate_identifier("users_table"), "users_table")

        with self.assertRaises(ValueError):
            _normalize_uuid("bad")
        with self.assertRaises(ValueError):
            _validate_identifier("1bad")
        with self.assertRaises(ValueError):
            _validate_identifier("bad-name")

    @patch("app_member.services.get_member_role_flags", side_effect=Exception("db"))
    def test_get_member_role_flags_safe_returns_default_on_missing_or_error(
        self, _get_flags
    ):
        self.assertEqual(get_member_role_flags_safe(None), MemberRoleFlags())
        self.assertEqual(
            get_member_role_flags_safe("11111111-1111-1111-1111-111111111111"),
            MemberRoleFlags(),
        )

    def test_search_directory_members_ignores_blank_search(self):
        self.assertEqual(search_directory_members("   "), [])

    def test_directory_member_search_result_shape(self):
        result = DirectoryMemberSearchResult(
            member_id="1",
            username="user",
            email=None,
            first_name=None,
            last_name=None,
            enabled=True,
            is_admin=False,
        )
        self.assertEqual(result.username, "user")

    @patch("app_member.services.SiteParams")
    def test_get_site_params_for_language_fallback_order(self, site_params_model):
        requested = object()
        fallback = object()
        first = object()
        filters = [
            Mock(first=Mock(return_value=None)),
            Mock(first=Mock(return_value=fallback)),
        ]
        site_params_model.objects.filter.side_effect = filters
        site_params_model.objects.order_by.return_value.first.return_value = first

        self.assertIs(services.get_site_params_for_language("en"), fallback)
        self.assertEqual(site_params_model.objects.filter.call_count, 2)

        site_params_model.objects.filter.reset_mock(side_effect=True)
        site_params_model.objects.filter.return_value.first.return_value = requested
        self.assertIs(services.get_site_params_for_language("fr"), requested)

    @patch("app_member.services.SiteParams")
    def test_get_site_params_for_language_returns_none_on_lookup_error(
        self, site_params_model
    ):
        site_params_model.objects.filter.side_effect = Exception("db")
        self.assertIsNone(services.get_site_params_for_language("fr"))

    @override_settings(USER_SCHEMA="users", USER_TABLE="users")
    def test_user_table_has_column_reads_information_schema(self):
        cursor = Mock()
        cursor.fetchone.return_value = (1,)
        cursor_context = Mock()
        cursor_context.__enter__ = Mock(return_value=cursor)
        cursor_context.__exit__ = Mock(return_value=False)

        with patch(
            "app_member.services.connection.cursor", return_value=cursor_context
        ):
            self.assertTrue(_user_table_has_column("enabled"))

        cursor.execute.assert_called_once()

    def test_get_member_role_flags_reads_member_admin_flag(self):
        member = Member(
            mm_id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
            is_admin=True,
        )
        queryset = Mock(first=Mock(return_value=member))

        with patch("app_member.services.Member.objects.filter", return_value=queryset):
            self.assertEqual(
                get_member_role_flags("11111111-1111-1111-1111-111111111111"),
                MemberRoleFlags(is_admin=True),
            )

        queryset.first.return_value = None
        with patch("app_member.services.Member.objects.filter", return_value=queryset):
            self.assertEqual(
                get_member_role_flags("11111111-1111-1111-1111-111111111111"),
                MemberRoleFlags(),
            )

    def test_set_member_role_validates_role_and_persists_admin_flag(self):
        member = Mock(is_admin=False)
        with self.assertRaises(ValidationError):
            set_member_role("11111111-1111-1111-1111-111111111111", "moderator", True)

        with patch(
            "app_member.services.Member.objects.get_or_create",
            return_value=(member, True),
        ):
            flags = set_member_role(
                "11111111-1111-1111-1111-111111111111",
                " ADMIN ",
                True,
            )

        self.assertEqual(flags, MemberRoleFlags(is_admin=True))
        member.full_clean.assert_called_once()
        member.save.assert_called_once()

    @override_settings(USER_SCHEMA="users", USER_TABLE="users")
    def test_search_directory_members_uses_directory_queryset_and_role_map(self):
        member_id = uuid.UUID("11111111-1111-1111-1111-111111111111")
        row = SimpleNamespace(
            id=member_id,
            username="alice",
            email="alice@example.test",
            first_name="Alice",
            last_name="Doe",
            enabled=True,
        )
        admin_member = Member(mm_id=member_id, is_admin=True)

        with (
            patch(
                "app_member.services._build_directory_user_queryset", return_value=[row]
            ),
            patch(
                "app_member.services.Member.objects.filter", return_value=[admin_member]
            ),
        ):
            results = search_directory_members(" alice ", limit=5)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].member_id, str(member_id))
        self.assertTrue(results[0].is_admin)

    @override_settings(USER_SCHEMA="external", USER_TABLE="people")
    def test_search_directory_members_can_use_raw_sql_fallback(self):
        member_id = "11111111-1111-1111-1111-111111111111"
        cursor = Mock()
        cursor.fetchall.return_value = [
            (member_id, None, "alice@example.test", "Alice", "Doe", 1)
        ]
        cursor_context = Mock()
        cursor_context.__enter__ = Mock(return_value=cursor)
        cursor_context.__exit__ = Mock(return_value=False)
        admin_member = Member(mm_id=uuid.UUID(member_id), is_admin=True)

        with (
            patch("app_member.services._user_table_has_column", return_value=False),
            patch("app_member.services.connection.cursor", return_value=cursor_context),
            patch(
                "app_member.services.Member.objects.filter", return_value=[admin_member]
            ),
        ):
            results = _search_directory_users_with_sql("alice", 10)

        self.assertEqual(results[0].username, "")
        self.assertEqual(results[0].email, "alice@example.test")
        self.assertTrue(results[0].enabled)
        self.assertTrue(results[0].is_admin)


class SiteParamsAdminFormTests(SimpleTestCase):
    def test_form_builds_home_card_payload_and_preserves_prefix_spaces(self):
        form = SiteParamsAdminForm(
            data={
                "title": "Animation Messe",
                "title_h1": "Animation Messe",
                "signup_url": "",
                "home_text": "",
                "bloc1_text": "Bloc 1",
                "bloc2_text": "Bloc 2",
                "admin_message_cooldown_minutes": "5",
                "home_card_1_title": " Accueil ",
                "home_card_1_text": " Préparer une animation ",
                "home_card_1_image": "home",
            }
        )

        self.assertTrue(form.is_valid(), form.errors)
        payload = json.loads(form.cleaned_data["home_text"])
        self.assertEqual(
            payload["cards"][0],
            {
                "title": "Accueil",
                "text": "Préparer une animation",
                "image": "home",
            },
        )

    def test_form_initializes_home_card_fields_from_existing_payload(self):
        instance = SiteParams(
            home_text=json.dumps(
                {
                    "cards": [
                        {
                            "title": "Titre",
                            "text": "Texte",
                            "image": "home",
                        }
                    ]
                }
            )
        )

        form = SiteParamsAdminForm(instance=instance)

        self.assertEqual(form.fields["home_card_1_title"].initial, "Titre")
        self.assertEqual(form.fields["home_card_1_text"].initial, "Texte")
        self.assertEqual(form.fields["home_card_1_image"].initial, "home")


class SitePopupContextProcessorTests(SimpleTestCase):
    def test_build_section_returns_empty_for_blank_message(self):
        self.assertEqual(context_processors._build_section("admin", "Title", "", 5), {})

    def test_build_section_hashes_message_and_normalizes_cooldown(self):
        section = context_processors._build_section("admin", "Title", " Hello ", "7")

        self.assertEqual(section["id"], "admin")
        self.assertEqual(section["messageMarkdown"], "Hello")
        self.assertEqual(section["cooldownMinutes"], 7)
        self.assertIn("version", section)

    @patch("app_member.context_processors.get_site_params_for_language")
    def test_site_popup_returns_admin_section_and_signup_url(self, get_params):
        get_params.return_value = type(
            "Params",
            (),
            {
                "signup_url": " https://signup.example ",
                "admin_message": "Message",
                "admin_message_cooldown_minutes": 3,
            },
        )()
        request = type("Request", (), {"LANGUAGE_CODE": "fr"})()

        context = context_processors.site_popup(request)
        payload = json.loads(context["lss_site_popup_json"])

        self.assertEqual(context["lss_signup_url"], "https://signup.example")
        self.assertEqual(payload["sections"][0]["id"], "admin")

    @patch(
        "app_member.context_processors.get_site_params_for_language",
        side_effect=Exception("db"),
    )
    def test_site_popup_tolerates_site_param_lookup_errors(self, _get_params):
        context = context_processors.site_popup(type("Request", (), {})())
        payload = json.loads(context["lss_site_popup_json"])

        self.assertEqual(context["lss_signup_url"], "")
        self.assertEqual(payload["sections"], [])
