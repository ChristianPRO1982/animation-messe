import json
import uuid

from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from app_member.forms import SiteParamsAdminForm
from app_member.models import (
    MemberPreferences,
    default_song_search,
    validate_song_search,
)
from app_member.services import (
    can_manage_moderator_popup,
    can_manage_site_members,
    can_manage_site_settings,
)


class MemberPreferencesTests(SimpleTestCase):
    def test_default_preferences_keep_shared_member_ui_contract(self):
        self.assertEqual(
            default_song_search(),
            {
                "text": "",
                "everywhere": False,
                "match_all_selected_refs": False,
                "genre_ids": [],
                "band_ids": [],
                "artist_ids": [],
                "validation": "all",
                "favorites_only": False,
            },
        )

        preferences = MemberPreferences(
            member_id=uuid.UUID("11111111-1111-1111-1111-111111111111")
        )
        self.assertEqual(preferences.theme_slug, "normal")
        self.assertEqual(preferences.song_search, default_song_search())

    def test_song_search_validation_rejects_invalid_payloads(self):
        with self.assertRaisesMessage(ValidationError, "objet JSON"):
            validate_song_search([])

        with self.assertRaisesMessage(ValidationError, "validation"):
            validate_song_search({**default_song_search(), "validation": "approved"})

        with self.assertRaisesMessage(ValidationError, "genre_ids"):
            validate_song_search({**default_song_search(), "genre_ids": ["1"]})


class PermissionHelperTests(SimpleTestCase):
    def test_permission_helpers_follow_admin_and_moderator_roles(self):
        admin_user = type(
            "User",
            (),
            {"is_authenticated": True, "is_admin": True, "is_moderator": True},
        )()
        moderator_user = type(
            "User",
            (),
            {"is_authenticated": True, "is_admin": False, "is_moderator": True},
        )()
        member_user = type(
            "User",
            (),
            {"is_authenticated": True, "is_admin": False, "is_moderator": False},
        )()

        self.assertTrue(can_manage_site_members(admin_user))
        self.assertTrue(can_manage_site_settings(admin_user))
        self.assertTrue(can_manage_moderator_popup(admin_user))
        self.assertFalse(can_manage_site_members(moderator_user))
        self.assertTrue(can_manage_moderator_popup(moderator_user))
        self.assertFalse(can_manage_site_members(member_user))
        self.assertFalse(can_manage_moderator_popup(member_user))


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
                "verse_max_lines": "4",
                "verse_max_characters_for_a_line": "42",
                "chorus_prefix": "  R.  ",
                "verse_prefix1": "  C",
                "verse_prefix2": ".  ",
                "admin_message_cooldown_minutes": "5",
                "moderator_message_cooldown_minutes": "60",
                "bg_img_max_bytes": "2097152",
                "bg_img_min_w": "800",
                "bg_img_min_h": "600",
                "bg_img_max_w": "4096",
                "bg_img_max_h": "3072",
                "bg_img_ratio_min": "1.3",
                "bg_img_ratio_max": "2.0",
                "bg_img_allowed_ext": ".jpg,.jpeg,.png",
                "bg_img_allowed_mime": "image/jpeg,image/png",
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
        self.assertEqual(form.cleaned_data["chorus_prefix"], "  R.  ")
        self.assertEqual(form.cleaned_data["verse_prefix1"], "  C")
        self.assertEqual(form.cleaned_data["verse_prefix2"], ".  ")
