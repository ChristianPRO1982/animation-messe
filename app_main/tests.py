from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase

from app_main.auth import (
    HOME_PROVISION_TARGET_SESSION_KEY,
    KEYCLOAK_DIAGNOSTIC_SESSION_KEY,
    KEYCLOAK_STATE_SESSION_KEY,
    PENDING_PROVISION_SESSION_KEY,
    SESSION_USER_KEY,
)
from app_main.views import AVAILABLE_THEMES


class ProjectSettingsTests(SimpleTestCase):
    def test_runtime_configuration_stays_wsgi_only(self):
        self.assertEqual(settings.WSGI_APPLICATION, "config.wsgi.application")
        self.assertFalse(hasattr(settings, "ASGI_APPLICATION"))
        self.assertNotIn("daphne", settings.INSTALLED_APPS)
        self.assertNotIn("channels", settings.INSTALLED_APPS)
        self.assertIn("whitenoise.middleware.WhiteNoiseMiddleware", settings.MIDDLEWARE)

    def test_core_apps_are_installed(self):
        self.assertIn("app_main", settings.INSTALLED_APPS)
        self.assertIn("app_member", settings.INSTALLED_APPS)

    def test_home_provision_defaults_target_animation_messe(self):
        self.assertEqual(settings.HOME_PROVISION_APP_ID, "am")
        self.assertIn(
            "redirect_am_secret.txt", settings.HOME_PROVISION_SHARED_SECRET_DEFAULT_FILE
        )


class SessionNamespaceTests(SimpleTestCase):
    def test_auth_session_keys_are_namespaced_for_am(self):
        self.assertEqual(SESSION_USER_KEY, "am_user")
        self.assertEqual(KEYCLOAK_STATE_SESSION_KEY, "am_keycloak_state")
        self.assertEqual(HOME_PROVISION_TARGET_SESSION_KEY, "am_home_provision_target")
        self.assertEqual(PENDING_PROVISION_SESSION_KEY, "am_pending_provision")
        self.assertEqual(KEYCLOAK_DIAGNOSTIC_SESSION_KEY, "am_keycloak_diagnostic")


class PublicPageTests(SimpleTestCase):
    def test_homepage_uses_animation_messe_fallback_title(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Animation Messe")

    def test_theme_page_exposes_expected_themes(self):
        response = self.client.get("/themes/")

        self.assertEqual(response.status_code, 200)
        for theme in ("normal", "scout", "taize", "me†al"):
            self.assertContains(response, theme)

    def test_available_themes_match_shared_theme_set(self):
        self.assertEqual(
            [theme["slug"] for theme in AVAILABLE_THEMES],
            ["normal", "scout", "taize", "me†al"],
        )


class AccountPageTemplateTests(SimpleTestCase):
    def test_account_page_does_not_render_technical_user_ids(self):
        template = (
            Path(settings.BASE_DIR)
            / "app_main"
            / "templates"
            / "main"
            / "connexion.html"
        ).read_text()

        self.assertNotIn("<p><code>{{ request.user.external_id }}</code></p>", template)
        self.assertNotIn("<p><code>{{ member.member_id }}</code></p>", template)
        self.assertIn('name="member_id" value="{{ member.member_id }}"', template)

    def test_account_summary_only_renders_first_and_last_name(self):
        template = (
            Path(settings.BASE_DIR)
            / "app_main"
            / "templates"
            / "main"
            / "connexion.html"
        ).read_text()
        summary_block = template.split("{% block page_summary %}", 1)[1].split(
            "{% endblock %}", 1
        )[0]

        self.assertIn(
            "{{ request.user.first_name }} {{ request.user.last_name }}", summary_block
        )
        self.assertNotIn("{{ account_heading }}", summary_block)
        self.assertNotIn("{{ request.user.username }}", summary_block)
