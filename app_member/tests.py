import json
import uuid

from django.test import SimpleTestCase

from app_member.forms import SiteParamsAdminForm
from app_member.models import Member, MemberPreferences
from app_member.services import (
    can_manage_site_members,
    can_manage_site_settings,
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
        self.assertFalse(can_manage_site_members(member_user))
        self.assertFalse(can_manage_site_settings(member_user))


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
