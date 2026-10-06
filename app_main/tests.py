import json
import tempfile
import time
from io import BytesIO
from pathlib import Path
from unittest.mock import Mock, patch
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlsplit

from django.conf import settings
from django.http import Http404, HttpResponse
from django.test import RequestFactory, SimpleTestCase, override_settings
from django.utils import timezone

from app_main import auth, views, wiki_help
from app_main.auth import (
    HOME_PROVISION_TARGET_SESSION_KEY,
    KEYCLOAK_DIAGNOSTIC_SESSION_KEY,
    KEYCLOAK_STATE_SESSION_KEY,
    PENDING_PROVISION_SESSION_KEY,
    SESSION_USER_KEY,
    AnonymousSessionUser,
    DirectoryUser,
    HomeProvisioningError,
    InvalidCallbackError,
    KeycloakAuthError,
    SessionUser,
    build_home_provision_start_url,
    build_keycloak_login_url,
    build_keycloak_logout_url,
    clear_pending_provision_state,
    clear_session_user,
    get_pending_provision_state,
    get_request_user,
    get_session_user,
    sign_callback_data,
    store_pending_provision_state,
    store_session_user,
    validate_callback_payload,
    validate_keycloak_callback,
)
from app_main.home_cards import (
    build_home_cards_payload,
    filter_display_home_cards,
    normalize_home_card_icon_slug,
    parse_home_cards,
)
from app_main.homepage_markdown import render_homepage_markdown
from app_main.models import SiteParams
from app_main.views import AVAILABLE_THEMES


class HelperSession(dict):
    modified = False

    def cycle_key(self):
        self["cycle_key_called"] = True
        self.modified = True


def build_request(factory, method="get", path="/", data=None, *, user=None):
    request_method = getattr(factory, method)
    request = request_method(path, data=data or {})
    request.session = HelperSession()
    request.user = (
        user
        or type(
            "User",
            (),
            {"is_authenticated": False, "is_admin": False, "username": ""},
        )()
    )
    request.LANGUAGE_CODE = "fr"
    return request


def build_user(*, authenticated=True, admin=False, username="tester"):
    return type(
        "User",
        (),
        {
            "is_authenticated": authenticated,
            "is_admin": admin,
            "username": username,
        },
    )()


def build_site_params(**overrides):
    values = {
        "language": "FR",
        "title": "Titre AM",
        "title_h1": "Titre H1",
        "signup_url": "",
        "home_text": "",
        "bloc1_text": "",
        "bloc2_text": "",
        "admin_message": "",
        "admin_message_cooldown_minutes": 5,
    }
    values.update(overrides)
    return SiteParams(**values)


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

    def test_public_navigation_exposes_groups_entry(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'href="/groups/"', count=2)
        self.assertContains(response, 'data-django-alias="groups"', count=2)
        self.assertContains(response, ">Groupes</span>")
        self.assertContains(response, 'data-theme-icon="groups"', count=2)
        self.assertContains(response, "icons/ui/normal/64/light/groups.png")

    def test_available_themes_match_shared_theme_set(self):
        self.assertEqual(
            [theme["slug"] for theme in AVAILABLE_THEMES],
            ["normal", "scout", "taize", "me†al"],
        )


class WikiHelpTests(SimpleTestCase):
    def test_all_routes_point_to_the_single_active_wiki_home(self):
        self.assertEqual(wiki_help.WIKI_PAGE_BY_URL_NAME, {})

        for url_name in (
            None,
            "",
            "homepage",
            "login",
            "groups_home",
            "site_params",
            "unknown",
        ):
            with self.subTest(url_name=url_name):
                self.assertEqual(
                    wiki_help.get_wiki_help_url(url_name),
                    wiki_help.WIKI_DEFAULT_URL,
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


class HomeCardsTests(SimpleTestCase):
    def test_icon_slug_normalization_accepts_known_icons_only(self):
        self.assertEqual(normalize_home_card_icon_slug(" home "), "home")
        self.assertEqual(normalize_home_card_icon_slug("missing"), "")
        self.assertEqual(normalize_home_card_icon_slug(None), "")

    def test_parse_home_cards_handles_empty_plain_text_and_invalid_payloads(self):
        self.assertEqual(parse_home_cards(""), [])
        self.assertEqual(
            parse_home_cards("Bienvenue"),
            [{"title": "", "text": "Bienvenue", "image": ""}],
        )
        self.assertEqual(parse_home_cards('{"cards": "bad"}'), [])
        self.assertEqual(parse_home_cards("[1, 2, 3]"), [])

    def test_parse_home_cards_normalizes_and_limits_cards(self):
        raw = {
            "cards": [
                {"title": " A ", "text": " B ", "image": "home"},
                {},
                "ignored",
                {"title": "C", "text": "", "image": "bad"},
                {"title": "D", "text": "E", "image": "theme"},
                {"title": "F", "text": "G", "image": "login"},
                {"title": "H", "text": "I", "image": "logout"},
                {"title": "Too far", "text": "ignored", "image": "home"},
            ]
        }

        cards = parse_home_cards(__import__("json").dumps(raw))

        self.assertEqual(len(cards), 4)
        self.assertEqual(cards[0], {"title": "A", "text": "B", "image": "home"})
        self.assertEqual(cards[1], {"title": "C", "text": "", "image": ""})
        self.assertNotIn("Too far", {card["title"] for card in cards})

    def test_filter_and_build_home_cards_payload(self):
        cards = [
            {"title": "A", "text": "B", "image": "home"},
            {"title": "No text", "text": "", "image": "theme"},
        ]

        self.assertEqual(filter_display_home_cards(cards), [cards[0]])
        self.assertEqual(
            parse_home_cards(build_home_cards_payload(cards)),
            [
                {"title": "A", "text": "B", "image": "home"},
                {"title": "No text", "text": "", "image": "theme"},
            ],
        )


class HomepageMarkdownTests(SimpleTestCase):
    def test_empty_markdown_renders_empty_string(self):
        self.assertEqual(str(render_homepage_markdown("")), "")
        self.assertEqual(str(render_homepage_markdown(None)), "")

    def test_markdown_renders_paragraph_quotes_inline_markup_and_escaping(self):
        rendered = str(
            render_homepage_markdown(
                "Bonjour **fort** et *doux* <script>\n> citation\n> suite\nRetour"
            )
        )

        self.assertIn("<strong>fort</strong>", rendered)
        self.assertIn("<em>doux</em>", rendered)
        self.assertIn("&lt;script&gt;", rendered)
        self.assertIn('blockquote class="site-home-markdown-quote"', rendered)
        self.assertIn("<br>", rendered)
        self.assertTrue(rendered.endswith("<p>Retour</p>"))


class AuthPayloadTests(SimpleTestCase):
    def _signed_payload(self, **overrides):
        payload = {
            "external_id": "11111111-1111-1111-1111-111111111111",
            "username": "testmock",
            "email": "test@example.test",
            "first_name": "Test",
            "last_name": "Mock",
            "ts": str(int(time.time())),
        }
        payload.update(overrides)
        payload["sig"] = sign_callback_data(payload, "secret")
        return payload

    @override_settings(AUTH_MOCK_SHARED_SECRET="secret", AUTH_MOCK_MAX_AGE_SECONDS=300)
    def test_validate_callback_payload_accepts_signed_payload(self):
        self.assertEqual(
            validate_callback_payload(self._signed_payload())["external_id"],
            "11111111-1111-1111-1111-111111111111",
        )

    @override_settings(AUTH_MOCK_SHARED_SECRET="secret", AUTH_MOCK_MAX_AGE_SECONDS=300)
    def test_validate_callback_payload_rejects_invalid_inputs(self):
        with self.assertRaises(InvalidCallbackError):
            validate_callback_payload({})
        with self.assertRaises(InvalidCallbackError):
            validate_callback_payload(self._signed_payload(ts="not-int"))
        with self.assertRaises(InvalidCallbackError):
            validate_callback_payload(self._signed_payload(ts="1"))
        with self.assertRaises(InvalidCallbackError):
            validate_callback_payload({**self._signed_payload(), "sig": "bad"})
        with self.assertRaises(InvalidCallbackError):
            validate_callback_payload(self._signed_payload(external_id="bad"))
        with self.assertRaises(InvalidCallbackError):
            validate_callback_payload(self._signed_payload(username="x" * 256))


class AuthHelperTests(SimpleTestCase):
    def test_session_user_properties_and_identifier_validation(self):
        user = SessionUser(
            external_id="1",
            username="alice",
            email=None,
            first_name=None,
            last_name=None,
        )
        anonymous = AnonymousSessionUser()

        self.assertTrue(user.is_authenticated)
        self.assertFalse(user.is_anonymous)
        self.assertEqual(user.get_username(), "alice")
        self.assertFalse(anonymous.is_authenticated)
        self.assertTrue(anonymous.is_anonymous)
        self.assertEqual(anonymous.get_username(), "")
        self.assertEqual(auth._validate_identifier("users_table"), "users_table")
        with self.assertRaises(ValueError):
            auth._validate_identifier("bad-name")

    @override_settings(
        HOME_PROVISION_START_URL="",
        HOME_PROVISION_APP_ID="am",
        HOME_PROVISION_SHARED_SECRET="secret",
        HOME_PROVISION_RETURN_URL="https://am.example/provision/complete/",
    )
    def test_build_home_provision_start_url_requires_complete_configuration(self):
        with self.assertRaises(HomeProvisioningError):
            build_home_provision_start_url()

    @override_settings(
        KEYCLOAK_CLIENT_ID="",
        KEYCLOAK_REDIRECT_URI="https://am.example/auth/callback/",
    )
    def test_build_keycloak_login_url_requires_client_configuration(self):
        with self.assertRaises(KeycloakAuthError):
            build_keycloak_login_url({})

    @override_settings(
        KEYCLOAK_CLIENT_ID="client",
        KEYCLOAK_LOGOUT_REDIRECT_URI="",
    )
    def test_build_keycloak_logout_url_requires_logout_configuration(self):
        with self.assertRaises(KeycloakAuthError):
            build_keycloak_logout_url()

    def test_keycloak_diagnostic_helpers_redact_and_parse_safe_data(self):
        request = auth.Request("https://kc.example/token?code=abc&client_secret=secret")
        self.assertEqual(auth._safe_request_url(request), "https://kc.example/token")
        self.assertEqual(auth._parse_keycloak_error_payload("not json"), ("", ""))
        self.assertEqual(auth._parse_keycloak_error_payload("[]"), ("", ""))

        error, description = auth._parse_keycloak_error_payload(
            '{"error":"invalid_client","error_description":"client_secret=secret"}'
        )

        self.assertEqual(error, "invalid_client")
        self.assertIn("[redacted]", description)
        self.assertIn(
            "[redacted]",
            auth._redact_keycloak_log_text('"access_token":"secret" code=abc'),
        )
        self.assertIn("échange", str(auth._keycloak_stage_label("token_exchange")))
        self.assertIn("profil", str(auth._keycloak_stage_label("userinfo")))
        self.assertIn("HTTP 500", str(auth._keycloak_http_error_message("other", 500)))

    def test_configured_file_exists_uses_env_and_default_paths(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            existing_file = Path(tmpdir) / "secret.txt"
            existing_file.write_text("secret")
            with patch.dict(
                "os.environ", {"AUTH_HELPER_SECRET_FILE": str(existing_file)}
            ):
                self.assertEqual(
                    auth._configured_file_exists("AUTH_HELPER_SECRET_FILE"),
                    (True, True),
                )

        with patch.dict("os.environ", {}, clear=True):
            self.assertEqual(
                auth._configured_file_exists("MISSING_SECRET_FILE"), (False, False)
            )
            self.assertEqual(
                auth._configured_file_exists("MISSING_SECRET_FILE", "/missing"),
                (True, False),
            )

    def test_build_keycloak_diagnostic_reports_secret_file_state(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            home_secret = Path(tmpdir) / "home.txt"
            home_secret.write_text("secret")
            with (
                patch.dict(
                    "os.environ", {"KEYCLOAK_CLIENT_SECRET_FILE": str(home_secret)}
                ),
                override_settings(
                    KEYCLOAK_CLIENT_SECRET="secret",
                    HOME_PROVISION_SHARED_SECRET_DEFAULT_FILE=str(home_secret),
                ),
            ):
                diagnostic = auth.build_keycloak_diagnostic(
                    stage="token_exchange",
                    message="KO",
                    status_code=401,
                    error="invalid_client",
                    safe_url="https://kc/token",
                )

        self.assertTrue(diagnostic["client_secret_configured"])
        self.assertTrue(diagnostic["client_secret_file_exists"])
        self.assertTrue(diagnostic["home_secret_file_exists"])

    def test_load_json_response_handles_success_and_keycloak_failures(self):
        class Response:
            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def read(self):
                return b'{"access_token":"token"}'

        request = auth.Request("https://kc.example/token?client_secret=secret")
        with patch("app_main.auth.urlopen", return_value=Response()):
            self.assertEqual(
                auth._load_json_response(request, stage="token_exchange"),
                {"access_token": "token"},
            )

        http_error = HTTPError(
            "https://kc.example/token?client_secret=secret",
            401,
            "Unauthorized",
            {},
            BytesIO(b'{"error":"invalid_client","error_description":"bad"}'),
        )
        with (
            patch("app_main.auth.urlopen", side_effect=http_error),
            self.assertRaises(KeycloakAuthError) as raised,
        ):
            auth._load_json_response(request, stage="token_exchange")
        self.assertEqual(raised.exception.diagnostic["status_code"], 401)

        with (
            patch("app_main.auth.urlopen", side_effect=URLError("offline")),
            self.assertRaises(KeycloakAuthError),
        ):
            auth._load_json_response(request, stage="userinfo")

        with (
            patch("app_main.auth.urlopen", side_effect=TimeoutError()),
            self.assertRaises(KeycloakAuthError),
        ):
            auth._load_json_response(request, stage="userinfo")

        class InvalidJsonResponse(Response):
            def read(self):
                return b"{"

        with (
            patch("app_main.auth.urlopen", return_value=InvalidJsonResponse()),
            self.assertRaises(KeycloakAuthError),
        ):
            auth._load_json_response(request, stage="userinfo")

    @override_settings(
        KEYCLOAK_SERVER_URL="https://kc.example",
        KEYCLOAK_REALM="am",
        KEYCLOAK_CLIENT_ID="client",
        KEYCLOAK_CLIENT_SECRET="secret",
        KEYCLOAK_REDIRECT_URI="https://am.example/auth/callback/",
    )
    def test_keycloak_exchange_and_userinfo_helpers_use_json_loader(self):
        with (
            patch("app_main.auth._load_json_response", return_value={}),
            self.assertRaises(KeycloakAuthError),
        ):
            auth._exchange_keycloak_code("code")

        with patch(
            "app_main.auth._load_json_response", return_value={"access_token": "token"}
        ):
            self.assertEqual(
                auth._exchange_keycloak_code("code"), {"access_token": "token"}
            )

        with patch(
            "app_main.auth._load_json_response", return_value={"sub": "id"}
        ) as loader:
            self.assertEqual(auth._fetch_keycloak_userinfo("token"), {"sub": "id"})
        self.assertEqual(loader.call_args.kwargs["stage"], "userinfo")

    @override_settings(KEYCLOAK_CLIENT_ID="", KEYCLOAK_CLIENT_SECRET="")
    def test_keycloak_exchange_requires_complete_configuration(self):
        with self.assertRaises(KeycloakAuthError):
            auth._exchange_keycloak_code("code")

    def test_validate_keycloak_callback_rejects_invalid_subject(self):
        session = {KEYCLOAK_STATE_SESSION_KEY: "state"}
        with (
            patch(
                "app_main.auth._exchange_keycloak_code",
                return_value={"access_token": "token"},
            ),
            patch(
                "app_main.auth._fetch_keycloak_userinfo", return_value={"sub": "bad"}
            ),
            self.assertRaises(KeycloakAuthError),
        ):
            validate_keycloak_callback({"code": "code", "state": "state"}, session)

    def test_directory_user_helpers_handle_records_and_lookup_errors(self):
        enabled_record = type(
            "Record",
            (),
            {
                "id": "11111111-1111-1111-1111-111111111111",
                "username": None,
                "email": None,
                "first_name": None,
                "last_name": None,
                "enabled": True,
            },
        )()
        disabled_record = type(
            "Record",
            (),
            {
                "id": "11111111-1111-1111-1111-111111111111",
                "username": "disabled",
                "email": None,
                "first_name": None,
                "last_name": None,
                "enabled": False,
            },
        )()

        self.assertEqual(auth._directory_user_from_record(enabled_record).username, "")
        with self.assertRaises(auth.DisabledUserError):
            auth._directory_user_from_record(disabled_record)
        with self.assertRaises(auth.UnknownUserError):
            auth.get_directory_user("bad")


class HomeProvisioningTests(SimpleTestCase):
    @override_settings(
        HOME_PROVISION_START_URL="https://carthographie.fr/provision/start",
        HOME_PROVISION_APP_ID="am",
        HOME_PROVISION_SHARED_SECRET="secret",
        HOME_PROVISION_RETURN_URL="https://am.carthographie.fr/provision/complete/",
    )
    @patch("app_main.auth.secrets.token_urlsafe", return_value="nonce")
    @patch("app_main.auth.time.time", return_value=123)
    def test_build_home_provision_start_url_signs_expected_payload(
        self, _time_mock, _token_mock
    ):
        url = build_home_provision_start_url()
        parsed = urlsplit(url)
        query = parse_qs(parsed.query)

        self.assertEqual(parsed.scheme, "https")
        self.assertEqual(query["app_id"], ["am"])
        self.assertEqual(
            query["return_url"], ["https://am.carthographie.fr/provision/complete/"]
        )
        self.assertEqual(query["ts"], ["123"])
        self.assertEqual(query["nonce"], ["nonce"])
        self.assertIn("sig", query)

    @override_settings(
        HOME_PROVISION_START_URL="https://carthographie.fr/provision/start",
        HOME_PROVISION_APP_ID="am",
        HOME_PROVISION_SHARED_SECRET="",
        HOME_PROVISION_RETURN_URL="https://am.carthographie.fr/provision/complete/",
    )
    def test_build_home_provision_start_url_requires_secret(self):
        with self.assertRaises(HomeProvisioningError):
            build_home_provision_start_url()

    @override_settings(HOME_PROVISION_RETURN_URL="http://am/provision/complete/")
    def test_home_provision_return_url_must_be_https_and_dedicated(self):
        with self.assertRaises(HomeProvisioningError):
            auth._validate_home_provision_return_url(settings.HOME_PROVISION_RETURN_URL)


class KeycloakHelperTests(SimpleTestCase):
    @override_settings(
        KEYCLOAK_SERVER_URL="https://kc.example",
        KEYCLOAK_REALM="am",
        KEYCLOAK_CLIENT_ID="client",
        KEYCLOAK_REDIRECT_URI="https://am.example/auth/callback/",
        KEYCLOAK_SCOPES="openid email",
    )
    @patch("app_main.auth.secrets.token_urlsafe", return_value="state")
    def test_build_keycloak_login_url_stores_state(self, _token_mock):
        session = {}
        url = build_keycloak_login_url(session)
        query = parse_qs(urlsplit(url).query)

        self.assertEqual(session[KEYCLOAK_STATE_SESSION_KEY], "state")
        self.assertEqual(query["client_id"], ["client"])
        self.assertEqual(query["state"], ["state"])

    @override_settings(
        KEYCLOAK_SERVER_URL="https://kc.example",
        KEYCLOAK_REALM="am",
        KEYCLOAK_CLIENT_ID="client",
        KEYCLOAK_LOGOUT_REDIRECT_URI="https://am.example/",
    )
    def test_build_keycloak_logout_url(self):
        self.assertIn("/logout?", build_keycloak_logout_url())

    @override_settings(KEYCLOAK_SERVER_URL="", KEYCLOAK_REALM="")
    def test_keycloak_base_url_requires_configuration(self):
        with self.assertRaises(KeycloakAuthError):
            auth._keycloak_oidc_base_url()

    def test_validate_keycloak_callback_rejects_error_missing_and_bad_state(self):
        with self.assertRaises(KeycloakAuthError):
            validate_keycloak_callback({"error": "access_denied"}, {})
        with self.assertRaises(KeycloakAuthError):
            validate_keycloak_callback({}, {})
        with self.assertRaises(KeycloakAuthError):
            validate_keycloak_callback(
                {"code": "c", "state": "bad"}, {KEYCLOAK_STATE_SESSION_KEY: "good"}
            )

    @patch(
        "app_main.auth._fetch_keycloak_userinfo",
        return_value={"sub": "11111111-1111-1111-1111-111111111111"},
    )
    @patch(
        "app_main.auth._exchange_keycloak_code", return_value={"access_token": "token"}
    )
    def test_validate_keycloak_callback_returns_external_identity(
        self, _exchange, _userinfo
    ):
        session = {KEYCLOAK_STATE_SESSION_KEY: "state"}

        payload = validate_keycloak_callback(
            {"code": "code", "state": "state"}, session
        )

        self.assertEqual(payload["external_id"], "11111111-1111-1111-1111-111111111111")
        self.assertNotIn(KEYCLOAK_STATE_SESSION_KEY, session)


class SessionAuthTests(SimpleTestCase):
    def test_store_get_and_clear_session_user(self):
        session = type("Session", (dict,), {"modified": False})()
        user = DirectoryUser(
            external_id="11111111-1111-1111-1111-111111111111",
            username="test",
            email="test@example.test",
            first_name="Test",
            last_name="User",
            enabled=True,
            is_admin=True,
        )

        store_session_user(session, user)
        self.assertTrue(session.modified)
        self.assertTrue(get_session_user(session)["is_admin"])
        self.assertIsInstance(get_request_user(session), SessionUser)

        clear_session_user(session)
        self.assertIsNone(get_session_user(session))
        self.assertIsInstance(get_request_user(session), AnonymousSessionUser)

    def test_pending_provision_state_validation(self):
        session = {}
        store_pending_provision_state(
            session,
            external_id="11111111-1111-1111-1111-111111111111",
        )
        self.assertEqual(get_pending_provision_state(session)["auth_mode"], "keycloak")

        session[PENDING_PROVISION_SESSION_KEY]["created_at"] = "bad"
        self.assertIsNone(get_pending_provision_state(session))

        session[PENDING_PROVISION_SESSION_KEY] = {
            "external_id": "",
            "auth_mode": "keycloak",
            "created_at": timezone.now().isoformat(),
        }
        self.assertIsNone(get_pending_provision_state(session))

        clear_pending_provision_state(session)
        self.assertIsNone(get_pending_provision_state(session))

    @patch("app_main.auth.get_member_role_flags_safe")
    @patch("app_main.auth.get_directory_user")
    def test_refresh_request_user_reloads_directory_and_roles(
        self, get_user, get_roles
    ):
        session = {
            SESSION_USER_KEY: {
                "external_id": "11111111-1111-1111-1111-111111111111",
                "username": "old",
            }
        }
        get_user.return_value = DirectoryUser(
            external_id="11111111-1111-1111-1111-111111111111",
            username="fresh",
            email=None,
            first_name=None,
            last_name=None,
            enabled=True,
        )
        get_roles.return_value = type("Roles", (), {"is_admin": True})()

        refreshed = auth.refresh_request_user(session)

        self.assertEqual(refreshed.username, "fresh")
        self.assertTrue(refreshed.is_admin)

    def test_refresh_request_user_clears_missing_external_id(self):
        session = {SESSION_USER_KEY: {"username": "broken"}}
        self.assertIsInstance(auth.refresh_request_user(session), AnonymousSessionUser)
        self.assertNotIn(SESSION_USER_KEY, session)


class MainViewHelperTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_homepage_builds_context_from_site_params(self):
        site_params = build_site_params(
            home_text=json.dumps(
                {"cards": [{"title": "Carte", "text": "**Texte**", "image": "home"}]}
            ),
            bloc1_text="Bloc 1",
            bloc2_text="Bloc 2",
        )
        request = build_request(self.factory)

        with (
            patch(
                "app_main.views.get_site_params_for_language", return_value=site_params
            ),
            patch("app_main.views.render", return_value=HttpResponse("ok")) as render,
        ):
            response = views.homepage(request)

        self.assertEqual(response.status_code, 200)
        context = render.call_args.args[2]
        self.assertEqual(context["home_site_title"], "Titre AM")
        self.assertEqual(context["home_cards"][0]["title"], "Carte")
        self.assertIn(
            "<strong>Texte</strong>", str(context["home_cards"][0]["rendered_text"])
        )
        self.assertIn("Bloc 1", str(context["home_bloc1_rendered"]))

    def test_collect_heavy_images_returns_am_and_static_urls(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "nested").mkdir()
            (root / "nested" / "image.png").write_bytes(b"png")
            (root / "note.txt").write_text("ignored")

            am_images = views._collect_heavy_images(root, source="am")
            static_images = views._collect_heavy_images(root, source="static")

        self.assertEqual(am_images[0]["relative_path"], "nested/image.png")
        self.assertIn("/heavy/assets/nested/image.png", am_images[0]["url"])
        self.assertIn("nested/image.png", static_images[0]["url"])
        self.assertEqual(views._collect_heavy_images(Path("/missing"), source="am"), [])

        with tempfile.NamedTemporaryFile() as file_root:
            self.assertEqual(
                views._collect_heavy_images(Path(file_root.name), source="am"), []
            )

    @override_settings(DEBUG=False)
    def test_heavy_is_debug_only(self):
        with self.assertRaises(Http404):
            views.heavy(build_request(self.factory, path="/heavy/"))

    @override_settings(DEBUG=True)
    def test_heavy_keeps_am_source_when_am_images_exist(self):
        request = build_request(self.factory, path="/heavy/")
        am_images = [
            {"name": "image.png", "relative_path": "image.png", "url": "/am/image.png"}
        ]

        with (
            patch("app_main.views._collect_heavy_images", return_value=am_images),
            patch("app_main.views.render", return_value=HttpResponse("ok")) as render,
        ):
            response = views.heavy(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(render.call_args.args[2]["image_source"], "AM")

    @override_settings(DEBUG=True)
    def test_heavy_uses_static_fallback_when_am_is_empty(self):
        request = build_request(self.factory, path="/heavy/")
        static_images = [
            {"name": "image.png", "relative_path": "image.png", "url": "/s/image.png"}
        ]

        with (
            patch(
                "app_main.views._collect_heavy_images", side_effect=[[], static_images]
            ),
            patch("app_main.views.render", return_value=HttpResponse("ok")) as render,
        ):
            response = views.heavy(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(render.call_args.args[2]["image_source"], "static")

    @override_settings(DEBUG=True)
    def test_heavy_asset_serves_allowed_image_inside_am_root(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir)
            image_path = base_dir / "AM" / "image.png"
            image_path.parent.mkdir()
            image_path.write_bytes(b"png")

            with override_settings(BASE_DIR=base_dir):
                response = views.heavy_asset(
                    build_request(self.factory, path="/heavy/assets/image.png"),
                    "image.png",
                )

        self.assertEqual(response.status_code, 200)
        response.close()

    @override_settings(DEBUG=False)
    def test_heavy_asset_is_debug_only(self):
        with self.assertRaises(Http404):
            views.heavy_asset(build_request(self.factory), "image.png")

    @override_settings(DEBUG=True)
    def test_heavy_asset_rejects_traversal_and_non_images(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir)
            (base_dir / "AM").mkdir()
            (base_dir / "AM" / "note.txt").write_text("text")

            with override_settings(BASE_DIR=base_dir):
                with self.assertRaises(Http404):
                    views.heavy_asset(build_request(self.factory), "../note.png")
                with self.assertRaises(Http404):
                    views.heavy_asset(build_request(self.factory), "note.txt")

    def test_account_redirect_preserves_normalized_search(self):
        response = views._account_redirect(build_request(self.factory), "  alice  ")
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response["Location"].endswith("/account/?member_search=alice"))

    def test_build_account_context_creates_default_forms_for_admin(self):
        request = build_request(
            self.factory, user=build_user(admin=True, username="alice")
        )

        context = views._build_account_context(
            request,
            current_language="fr",
            site_params=build_site_params(),
            member_search="alice",
        )

        self.assertTrue(context["is_admin"])
        self.assertEqual(context["member_results"], [])
        self.assertIsNotNone(context["member_search_form"])
        self.assertIsNotNone(context["admin_message_form"])

    def test_keycloak_diagnostic_causes_cover_known_error_shapes(self):
        self.assertTrue(
            views._keycloak_diagnostic_causes(
                {
                    "stage": "token_exchange",
                    "status_code": 401,
                    "error": "invalid_client",
                }
            )
        )
        self.assertTrue(
            views._keycloak_diagnostic_causes(
                {
                    "stage": "token_exchange",
                    "status_code": 400,
                    "error": "invalid_grant",
                }
            )
        )
        self.assertTrue(
            views._keycloak_diagnostic_causes({"stage": "userinfo", "status_code": 401})
        )
        self.assertEqual(views._keycloak_diagnostic_causes({}), [])
        self.assertTrue(views._keycloak_diagnostic_causes({"stage": "other"}))


class LoginAndProvisionViewTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_login_redirects_authenticated_users_to_account(self):
        request = build_request(self.factory, path="/login/", user=build_user())

        response = views.login(request)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response["Location"].endswith("/account/"))

    @override_settings(AUTH_MODE="mock", AUTH_MOCK_BASE_URL="https://mock.example")
    def test_login_start_redirects_to_mock_provider(self):
        request = build_request(self.factory, path="/login/?start=1")

        response = views.login(request)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response["Location"].startswith("https://mock.example/login?"))

    @override_settings(AUTH_MODE="disabled")
    def test_login_refuses_unsupported_auth_mode(self):
        request = build_request(self.factory, path="/login/")

        with patch("app_main.views.messages") as message_api:
            response = views.login(request)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response["Location"].endswith("/"))
        message_api.error.assert_called_once()

    @override_settings(AUTH_MODE="keycloak")
    def test_login_start_redirects_to_keycloak_provider(self):
        request = build_request(self.factory, path="/login/?start=1")

        with patch(
            "app_main.views.build_keycloak_login_url",
            return_value="https://kc.example/auth",
        ) as build_url:
            response = views.login(request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "https://kc.example/auth")
        build_url.assert_called_once_with(request.session)

    @override_settings(AUTH_MODE="keycloak")
    def test_login_start_stores_diagnostic_on_keycloak_configuration_error(self):
        request = build_request(self.factory, path="/login/?start=1")

        with (
            patch(
                "app_main.views.build_keycloak_login_url",
                side_effect=KeycloakAuthError(
                    "config KO", diagnostic={"stage": "auth"}
                ),
            ),
            patch("app_main.views.messages") as message_api,
        ):
            response = views.login(request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            request.session[KEYCLOAK_DIAGNOSTIC_SESSION_KEY]["stage"], "auth"
        )
        message_api.error.assert_called_once()

    def test_store_keycloak_diagnostic_builds_fallback_diagnostic(self):
        request = build_request(self.factory)

        with patch(
            "app_main.views.build_keycloak_diagnostic",
            return_value={"stage": "callback"},
        ) as build_diagnostic:
            views._store_keycloak_diagnostic(request, KeycloakAuthError("KO"))

        build_diagnostic.assert_called_once()
        self.assertEqual(
            request.session[KEYCLOAK_DIAGNOSTIC_SESSION_KEY]["stage"], "callback"
        )

    def test_login_page_renders_login_mode(self):
        request = build_request(self.factory, path="/login/")

        with patch("app_main.views.render", return_value=HttpResponse("ok")) as render:
            response = views.login(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(render.call_args.args[2]["page_mode"], "login")

    @override_settings(AUTH_MODE="mock")
    def test_auth_callback_invalid_payload_clears_session(self):
        request = build_request(self.factory, path="/auth/callback/")
        request.session[SESSION_USER_KEY] = {"username": "old"}

        with (
            patch(
                "app_main.views.validate_callback_payload",
                side_effect=InvalidCallbackError("bad callback"),
            ),
            patch("app_main.views.messages") as message_api,
        ):
            response = views.auth_callback(request)

        self.assertEqual(response.status_code, 302)
        self.assertNotIn(SESSION_USER_KEY, request.session)
        message_api.error.assert_called_once()

    @override_settings(AUTH_MODE="mock")
    def test_auth_callback_success_stores_session_user(self):
        request = build_request(self.factory, path="/auth/callback/")
        user = DirectoryUser(
            external_id="11111111-1111-1111-1111-111111111111",
            username="alice",
            email=None,
            first_name=None,
            last_name=None,
            enabled=True,
            is_admin=True,
        )

        with (
            patch(
                "app_main.views.validate_callback_payload",
                return_value={"external_id": user.external_id},
            ),
            patch("app_main.views.get_directory_user", return_value=user),
            patch("app_main.views.messages"),
        ):
            response = views.auth_callback(request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(request.session[SESSION_USER_KEY]["username"], "alice")
        self.assertTrue(request.session["cycle_key_called"])

    @override_settings(AUTH_MODE="keycloak")
    def test_auth_callback_unknown_keycloak_user_starts_home_provisioning(self):
        request = build_request(self.factory, path="/auth/callback/")

        with (
            patch(
                "app_main.views.validate_keycloak_callback",
                return_value={"external_id": "11111111-1111-1111-1111-111111111111"},
            ),
            patch(
                "app_main.views.get_directory_user",
                side_effect=auth.UnknownUserError("missing"),
            ),
            patch(
                "app_main.views.build_home_provision_start_url",
                return_value="https://home/provision",
            ),
            patch("app_main.views.messages"),
        ):
            response = views.auth_callback(request)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response["Location"].endswith("/provision/redirect/"))
        self.assertEqual(
            request.session[HOME_PROVISION_TARGET_SESSION_KEY],
            "https://home/provision",
        )
        self.assertEqual(
            request.session[PENDING_PROVISION_SESSION_KEY]["external_id"],
            "11111111-1111-1111-1111-111111111111",
        )

    @override_settings(AUTH_MODE="keycloak")
    def test_auth_callback_records_keycloak_errors(self):
        request = build_request(self.factory, path="/auth/callback/")

        with (
            patch(
                "app_main.views.validate_keycloak_callback",
                side_effect=KeycloakAuthError(
                    "kc KO", diagnostic={"stage": "userinfo"}
                ),
            ),
            patch("app_main.views.messages") as message_api,
        ):
            response = views.auth_callback(request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            request.session[KEYCLOAK_DIAGNOSTIC_SESSION_KEY]["stage"],
            "userinfo",
        )
        message_api.error.assert_called_once()

    @override_settings(AUTH_MODE="disabled")
    def test_auth_callback_rejects_unsupported_auth_mode(self):
        request = build_request(self.factory, path="/auth/callback/")

        with patch("app_main.views.messages") as message_api:
            response = views.auth_callback(request)

        self.assertEqual(response.status_code, 302)
        message_api.error.assert_called_once()

    @override_settings(AUTH_MODE="mock")
    def test_auth_callback_unknown_mock_user_returns_home(self):
        request = build_request(
            self.factory, path="/auth/callback/?external_id=external"
        )

        with (
            patch(
                "app_main.views.validate_callback_payload",
                return_value={"external_id": "11111111-1111-1111-1111-111111111111"},
            ),
            patch(
                "app_main.views.get_directory_user",
                side_effect=auth.UnknownUserError("missing"),
            ),
            patch("app_main.views.messages") as message_api,
        ):
            response = views.auth_callback(request)

        self.assertEqual(response.status_code, 302)
        message_api.error.assert_called_once()

    @override_settings(AUTH_MODE="mock")
    def test_auth_callback_disabled_user_returns_home(self):
        request = build_request(
            self.factory, path="/auth/callback/?external_id=external"
        )

        with (
            patch(
                "app_main.views.validate_callback_payload",
                return_value={"external_id": "11111111-1111-1111-1111-111111111111"},
            ),
            patch(
                "app_main.views.get_directory_user",
                side_effect=auth.DisabledUserError("disabled"),
            ),
            patch("app_main.views.messages") as message_api,
        ):
            response = views.auth_callback(request)

        self.assertEqual(response.status_code, 302)
        message_api.error.assert_called_once()

    @override_settings(AUTH_MODE="keycloak")
    def test_auth_callback_clears_pending_state_when_home_provisioning_url_fails(self):
        request = build_request(self.factory, path="/auth/callback/")
        request.session[PENDING_PROVISION_SESSION_KEY] = {"external_id": "old"}
        request.session[HOME_PROVISION_TARGET_SESSION_KEY] = "https://old"

        with (
            patch(
                "app_main.views.validate_keycloak_callback",
                return_value={"external_id": "11111111-1111-1111-1111-111111111111"},
            ),
            patch(
                "app_main.views.get_directory_user",
                side_effect=auth.UnknownUserError("missing"),
            ),
            patch(
                "app_main.views.build_home_provision_start_url",
                side_effect=HomeProvisioningError("no provisioning"),
            ),
            patch("app_main.views.messages") as message_api,
        ):
            response = views.auth_callback(request)

        self.assertEqual(response.status_code, 302)
        self.assertNotIn(PENDING_PROVISION_SESSION_KEY, request.session)
        self.assertNotIn(HOME_PROVISION_TARGET_SESSION_KEY, request.session)
        message_api.error.assert_called_once()

    def test_keycloak_diagnostic_renders_session_diagnostic(self):
        request = build_request(self.factory, path="/login/diagnostic/")
        request.session[KEYCLOAK_DIAGNOSTIC_SESSION_KEY] = {
            "stage": "userinfo",
            "status_code": 401,
        }

        with patch("app_main.views.render", return_value=HttpResponse("ok")) as render:
            response = views.keycloak_diagnostic(request)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(render.call_args.args[2]["causes"])

    def test_provision_redirect_without_target_goes_home(self):
        request = build_request(self.factory, path="/provision/redirect/")

        with patch("app_main.views.messages") as message_api:
            response = views.provision_redirect(request)

        self.assertEqual(response.status_code, 302)
        message_api.info.assert_called_once()

    def test_provision_redirect_renders_target_once(self):
        request = build_request(self.factory, path="/provision/redirect/")
        request.session[HOME_PROVISION_TARGET_SESSION_KEY] = "https://home/provision"

        with patch("app_main.views.render", return_value=HttpResponse("ok")) as render:
            response = views.provision_redirect(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            render.call_args.args[2]["provision_url"], "https://home/provision"
        )
        self.assertNotIn(HOME_PROVISION_TARGET_SESSION_KEY, request.session)

    def test_provision_complete_without_pending_state_goes_home(self):
        request = build_request(self.factory, path="/provision/complete/")

        with patch("app_main.views.messages") as message_api:
            response = views.provision_complete(request)

        self.assertEqual(response.status_code, 302)
        message_api.info.assert_called_once()

    def test_provision_complete_renders_waiting_page_when_user_is_still_missing(self):
        request = build_request(self.factory, path="/provision/complete/")
        store_pending_provision_state(
            request.session,
            external_id="11111111-1111-1111-1111-111111111111",
        )

        with (
            patch(
                "app_main.views.get_directory_user",
                side_effect=auth.UnknownUserError("missing"),
            ),
            patch("app_main.views.render", return_value=HttpResponse("ok")) as render,
        ):
            response = views.provision_complete(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(render.call_args.args[1], "main/provision_complete.html")

    def test_provision_complete_success_logs_user_in(self):
        request = build_request(self.factory, path="/provision/complete/")
        store_pending_provision_state(
            request.session,
            external_id="11111111-1111-1111-1111-111111111111",
        )
        user = DirectoryUser(
            external_id="11111111-1111-1111-1111-111111111111",
            username="alice",
            email=None,
            first_name=None,
            last_name=None,
            enabled=True,
        )

        with (
            patch("app_main.views.get_directory_user", return_value=user),
            patch("app_main.views.messages"),
        ):
            response = views.provision_complete(request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(request.session[SESSION_USER_KEY]["username"], "alice")
        self.assertNotIn(PENDING_PROVISION_SESSION_KEY, request.session)

    def test_provision_complete_disabled_user_clears_state(self):
        request = build_request(self.factory, path="/provision/complete/")
        store_pending_provision_state(
            request.session,
            external_id="11111111-1111-1111-1111-111111111111",
        )
        request.session[HOME_PROVISION_TARGET_SESSION_KEY] = "https://home"
        request.session[SESSION_USER_KEY] = {"username": "old"}

        with (
            patch(
                "app_main.views.get_directory_user",
                side_effect=auth.DisabledUserError("disabled"),
            ),
            patch("app_main.views.messages") as message_api,
        ):
            response = views.provision_complete(request)

        self.assertEqual(response.status_code, 302)
        self.assertNotIn(PENDING_PROVISION_SESSION_KEY, request.session)
        self.assertNotIn(HOME_PROVISION_TARGET_SESSION_KEY, request.session)
        self.assertNotIn(SESSION_USER_KEY, request.session)
        message_api.error.assert_called_once()

    @override_settings(AUTH_MODE="keycloak")
    def test_logout_clears_state_and_redirects_to_keycloak_when_available(self):
        request = build_request(self.factory, path="/logout/")
        store_session_user(
            request.session,
            DirectoryUser(
                external_id="11111111-1111-1111-1111-111111111111",
                username="alice",
                email=None,
                first_name=None,
                last_name=None,
                enabled=True,
            ),
        )
        request.session[PENDING_PROVISION_SESSION_KEY] = {"external_id": "x"}
        request.session[HOME_PROVISION_TARGET_SESSION_KEY] = "https://home"

        with (
            patch(
                "app_main.views.build_keycloak_logout_url",
                return_value="https://kc/logout",
            ),
            patch("app_main.views.messages"),
        ):
            response = views.logout(request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "https://kc/logout")
        self.assertNotIn(SESSION_USER_KEY, request.session)

    @override_settings(AUTH_MODE="keycloak")
    def test_logout_falls_back_home_when_keycloak_logout_url_fails(self):
        request = build_request(self.factory, path="/logout/")

        with (
            patch(
                "app_main.views.build_keycloak_logout_url",
                side_effect=KeycloakAuthError("logout KO"),
            ),
            patch("app_main.views.messages"),
        ):
            response = views.logout(request)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response["Location"].endswith("/"))


class AccountAndSettingsViewTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_account_requires_authentication(self):
        response = views.account(build_request(self.factory, path="/account/"))

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response["Location"].endswith("/login/"))

    def test_account_get_searches_members_for_admin(self):
        request = build_request(
            self.factory,
            path="/account/?member_search=alice",
            user=build_user(admin=True),
        )
        result = Mock(username="alice")

        with (
            patch(
                "app_main.views.get_site_params_for_language",
                return_value=build_site_params(),
            ),
            patch(
                "app_main.views.search_directory_members", return_value=[result]
            ) as search,
            patch("app_main.views.render", return_value=HttpResponse("ok")) as render,
        ):
            response = views.account(request)

        self.assertEqual(response.status_code, 200)
        search.assert_called_once_with("alice")
        self.assertEqual(render.call_args.args[2]["member_results"], [result])
        self.assertTrue(render.call_args.args[2]["is_admin"])

    def test_account_post_save_admin_message_requires_admin(self):
        request = build_request(
            self.factory,
            method="post",
            path="/account/",
            data={"action": "save_admin_message_settings"},
            user=build_user(admin=False),
        )

        with patch(
            "app_main.views.get_site_params_for_language",
            return_value=build_site_params(),
        ):
            response = views.account(request)

        self.assertEqual(response.status_code, 403)

    def test_account_post_saves_admin_message_settings(self):
        request = build_request(
            self.factory,
            method="post",
            path="/account/",
            data={"action": "save_admin_message_settings", "member_search": "alice"},
            user=build_user(admin=True),
        )
        form = Mock(is_valid=Mock(return_value=True), save=Mock())

        with (
            patch(
                "app_main.views.get_site_params_for_language",
                return_value=build_site_params(),
            ),
            patch("app_main.views.AdminMessageForm", return_value=form),
            patch("app_main.views.messages") as message_api,
        ):
            response = views.account(request)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response["Location"].endswith("/account/?member_search=alice"))
        form.save.assert_called_once()
        message_api.success.assert_called_once()

    def test_account_post_admin_message_reports_missing_site_params(self):
        request = build_request(
            self.factory,
            method="post",
            path="/account/",
            data={"action": "save_admin_message_settings", "member_search": "alice"},
            user=build_user(admin=True),
        )

        with (
            patch("app_main.views.get_site_params_for_language", return_value=None),
            patch("app_main.views.messages") as message_api,
        ):
            response = views.account(request)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response["Location"].endswith("/account/?member_search=alice"))
        message_api.error.assert_called_once()

    def test_account_post_invalid_admin_message_form_rerenders_context(self):
        request = build_request(
            self.factory,
            method="post",
            path="/account/",
            data={"action": "save_admin_message_settings", "member_search": "alice"},
            user=build_user(admin=True),
        )
        form = Mock(is_valid=Mock(return_value=False))
        result = Mock(username="alice")

        with (
            patch(
                "app_main.views.get_site_params_for_language",
                return_value=build_site_params(),
            ),
            patch("app_main.views.AdminMessageForm", return_value=form),
            patch("app_main.views.search_directory_members", return_value=[result]),
            patch("app_main.views.render", return_value=HttpResponse("ok")) as render,
        ):
            response = views.account(request)

        self.assertEqual(response.status_code, 200)
        self.assertIs(render.call_args.args[2]["admin_message_form"], form)
        self.assertEqual(render.call_args.args[2]["member_results"], [result])

    def test_account_post_updates_member_role(self):
        member_id = "11111111-1111-1111-1111-111111111111"
        request = build_request(
            self.factory,
            method="post",
            path="/account/",
            data={
                "action": "update_member_role",
                "member_id": member_id,
                "role_name": "admin",
                "enabled": "on",
                "member_search": "alice",
            },
            user=build_user(admin=True),
        )

        with (
            patch(
                "app_main.views.get_site_params_for_language",
                return_value=build_site_params(),
            ),
            patch("app_main.views.set_member_role") as set_role,
            patch("app_main.views.messages"),
        ):
            response = views.account(request)

        self.assertEqual(response.status_code, 302)
        set_role.assert_called_once_with(
            member_id=member_id,
            role_name="admin",
            enabled=True,
        )

    def test_account_post_update_member_role_requires_admin(self):
        request = build_request(
            self.factory,
            method="post",
            path="/account/",
            data={"action": "update_member_role"},
            user=build_user(admin=False),
        )

        with patch(
            "app_main.views.get_site_params_for_language",
            return_value=build_site_params(),
        ):
            response = views.account(request)

        self.assertEqual(response.status_code, 403)

    def test_account_post_removes_member_role(self):
        member_id = "11111111-1111-1111-1111-111111111111"
        request = build_request(
            self.factory,
            method="post",
            path="/account/",
            data={
                "action": "update_member_role",
                "member_id": member_id,
                "role_name": "admin",
                "member_search": "alice",
            },
            user=build_user(admin=True),
        )

        with (
            patch(
                "app_main.views.get_site_params_for_language",
                return_value=build_site_params(),
            ),
            patch("app_main.views.set_member_role") as set_role,
            patch("app_main.views.messages") as message_api,
        ):
            response = views.account(request)

        self.assertEqual(response.status_code, 302)
        set_role.assert_called_once_with(
            member_id=member_id,
            role_name="admin",
            enabled=False,
        )
        message_api.success.assert_called_once()

    def test_account_post_invalid_member_role_form_rerenders_context(self):
        request = build_request(
            self.factory,
            method="post",
            path="/account/",
            data={"action": "update_member_role", "member_search": "alice"},
            user=build_user(admin=True),
        )
        result = Mock(username="alice")

        with (
            patch(
                "app_main.views.get_site_params_for_language",
                return_value=build_site_params(),
            ),
            patch("app_main.views.search_directory_members", return_value=[result]),
            patch("app_main.views.messages") as message_api,
            patch("app_main.views.render", return_value=HttpResponse("ok")) as render,
        ):
            response = views.account(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(render.call_args.args[2]["member_results"], [result])
        message_api.error.assert_called_once()

    def test_account_post_unknown_action_redirects_with_message(self):
        request = build_request(
            self.factory,
            method="post",
            path="/account/",
            data={"action": "wat", "member_search": "alice"},
            user=build_user(admin=True),
        )

        with (
            patch(
                "app_main.views.get_site_params_for_language",
                return_value=build_site_params(),
            ),
            patch("app_main.views.messages") as message_api,
        ):
            response = views.account(request)

        self.assertEqual(response.status_code, 302)
        message_api.error.assert_called_once()

    def test_site_params_requires_admin(self):
        unauthenticated = views.site_params(
            build_request(self.factory, path="/site-params/")
        )
        self.assertEqual(unauthenticated.status_code, 302)

        with self.assertRaises(Http404):
            views.site_params(
                build_request(
                    self.factory,
                    path="/site-params/",
                    user=build_user(admin=False),
                )
            )

    def test_site_params_get_builds_admin_form_for_selected_language(self):
        request = build_request(
            self.factory,
            path="/site-params/?language=en",
            user=build_user(admin=True),
        )
        query = Mock(first=Mock(return_value=None))
        form = Mock()

        with (
            patch("app_main.views.SiteParams.objects.filter", return_value=query),
            patch("app_main.views.SiteParamsAdminForm", return_value=form),
            patch("app_main.views.render", return_value=HttpResponse("ok")) as render,
        ):
            response = views.site_params(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(render.call_args.args[2]["selected_language"], "en")
        self.assertIs(render.call_args.args[2]["admin_form"], form)

    def test_site_params_get_normalizes_unknown_language_to_french(self):
        request = build_request(
            self.factory,
            path="/site-params/?language=zz",
            user=build_user(admin=True),
        )
        query = Mock(first=Mock(return_value=build_site_params(language="FR")))

        with (
            patch("app_main.views.SiteParams.objects.filter", return_value=query),
            patch("app_main.views.SiteParamsAdminForm", return_value=Mock()),
            patch("app_main.views.render", return_value=HttpResponse("ok")) as render,
        ):
            response = views.site_params(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(render.call_args.args[2]["selected_language"], "fr")

    def test_site_params_post_saves_valid_form(self):
        request = build_request(
            self.factory,
            method="post",
            path="/site-params/",
            data={"language": "en"},
            user=build_user(admin=True),
        )
        query = Mock(first=Mock(return_value=None))
        saved = Mock(save=Mock())
        form = Mock(is_valid=Mock(return_value=True), save=Mock(return_value=saved))

        with (
            patch("app_main.views.SiteParams.objects.filter", return_value=query),
            patch("app_main.views.SiteParamsAdminForm", return_value=form),
        ):
            response = views.site_params(request)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response["Location"].endswith("/site-params/?language=en"))
        self.assertEqual(saved.language, "EN")
        saved.save.assert_called_once()

    def test_site_params_post_reports_invalid_fields(self):
        request = build_request(
            self.factory,
            method="post",
            path="/site-params/",
            data={"language": "xx"},
            user=build_user(admin=True),
        )
        query = Mock(first=Mock(return_value=None))
        form = Mock(
            is_valid=Mock(return_value=False),
            errors={"title": ["required"]},
            fields={"title": Mock(label="Titre du site")},
        )

        with (
            patch("app_main.views.SiteParams.objects.filter", return_value=query),
            patch("app_main.views.SiteParamsAdminForm", return_value=form),
            patch("app_main.views.messages") as message_api,
            patch("app_main.views.render", return_value=HttpResponse("ok")),
        ):
            response = views.site_params(request)

        self.assertEqual(response.status_code, 200)
        message_api.error.assert_called_once()

    def test_site_params_post_reports_generic_invalid_form_without_field_errors(self):
        request = build_request(
            self.factory,
            method="post",
            path="/site-params/",
            data={"language": "fr"},
            user=build_user(admin=True),
        )
        query = Mock(first=Mock(return_value=None))
        form = Mock(is_valid=Mock(return_value=False), errors={}, fields={})

        with (
            patch("app_main.views.SiteParams.objects.filter", return_value=query),
            patch("app_main.views.SiteParamsAdminForm", return_value=form),
            patch("app_main.views.messages") as message_api,
            patch("app_main.views.render", return_value=HttpResponse("ok")),
        ):
            response = views.site_params(request)

        self.assertEqual(response.status_code, 200)
        message_api.error.assert_called_once()

    def test_static_preference_pages_render_context(self):
        request = build_request(self.factory, path="/themes/")

        with patch("app_main.views.render", return_value=HttpResponse("ok")) as render:
            views.privacy_policy(request)
            views.theme_preferences(request)
            views.language_preferences(request)

        templates = [call.args[1] for call in render.call_args_list]
        self.assertEqual(
            templates,
            [
                "main/privacy_policy.html",
                "main/theme_preferences.html",
                "main/language.html",
            ],
        )
