from html.parser import HTMLParser
from pathlib import Path
from types import SimpleNamespace

from django.conf import settings
from django.template import Context, Engine
from django.template.loader import render_to_string
from django.test import SimpleTestCase
from django.utils.translation import gettext, override


class PageToolsParser(HTMLParser):
    """Inspect tools independently of identical navigation links elsewhere."""

    def __init__(self, html):
        super().__init__()
        self.tools_depth = 0
        self.tools_elements = []
        self.tools_text = []
        self.toggles = []
        self.tools_count = 0
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "data-mobile-actions-toggle" in attrs:
            self.toggles.append(attrs)
        if "data-page-tools" in attrs:
            self.tools_count += 1
            self.tools_depth = 1
        elif self.tools_depth:
            self.tools_elements.append((tag, attrs))
            if tag not in {
                "area",
                "base",
                "br",
                "col",
                "embed",
                "hr",
                "img",
                "input",
                "link",
                "meta",
                "param",
                "source",
                "track",
                "wbr",
            }:
                self.tools_depth += 1

    def handle_endtag(self, tag):
        if self.tools_depth:
            self.tools_depth -= 1

    def handle_data(self, data):
        if self.tools_depth:
            self.tools_text.append(data)

    @property
    def links(self):
        return [attrs for tag, attrs in self.tools_elements if tag == "a"]


class PageToolsTemplateTests(SimpleTestCase):
    def render_page(self, name, **context):
        return render_to_string(name, context)

    def test_base_exposes_one_shared_region_and_a_non_submitting_toggle(self):
        html = self.render_page("base.html")
        parsed = PageToolsParser(html)
        self.assertEqual(parsed.tools_count, 1)
        self.assertEqual(len(parsed.toggles), 1)
        self.assertEqual(parsed.toggles[0]["type"], "button")
        self.assertEqual(parsed.toggles[0]["aria-controls"], "site-page-tools")
        self.assertEqual(parsed.toggles[0]["aria-expanded"], "false")
        self.assertIn("data-mobile-actions hidden", html)
        self.assertEqual("".join(parsed.tools_text).strip(), "")

    def test_toggle_labels_use_django_translations(self):
        for language, labels in (
            ("fr", ("Afficher les actions", "Masquer les actions")),
            ("en", ("Show actions", "Hide actions")),
        ):
            with self.subTest(language=language), override(language):
                toggle = PageToolsParser(self.render_page("base.html")).toggles[0]
                # Fresh checkouts may only contain PO sources. Check runtime
                # labels and translation sources without requiring compiled MOs.
                sources = ("Afficher les actions", "Masquer les actions")
                self.assertEqual(toggle["data-open-label"], gettext(sources[0]))
                self.assertEqual(toggle["data-close-label"], gettext(sources[1]))
                catalog = (
                    Path(settings.BASE_DIR)
                    / "locale"
                    / language
                    / "LC_MESSAGES/django.po"
                ).read_text()
                for source, label in zip(sources, labels):
                    self.assertIn(f'msgid "{source}"\nmsgstr "{label}"', catalog)

    def test_external_submit_buttons_and_separators_are_rendered_once(self):
        template = Engine.get_default().from_string("""{% extends "base.html" %}
            {% block page_tools %}
                <a href="/back/">Retour</a><hr>
                <button type="submit" form="editor" name="intent" value="save">Enregistrer</button>
                <button type="submit" form="editor" name="intent" value="exit">Quitter</button>
            {% endblock %}
            {% block content %}<form id="editor" method="post"></form>{% endblock %}""")
        html = template.render(Context())
        parsed = PageToolsParser(html)
        buttons = [attrs for tag, attrs in parsed.tools_elements if tag == "button"]
        self.assertEqual(
            [(button["form"], button["name"], button["value"]) for button in buttons],
            [("editor", "intent", "save"), ("editor", "intent", "exit")],
        )
        self.assertEqual(sum(tag == "hr" for tag, _ in parsed.tools_elements), 1)
        self.assertEqual(html.count('value="save"'), 1)
        self.assertEqual(html.count('value="exit"'), 1)

    def test_group_dashboard_tools_keep_role_visibility(self):
        for role in ("member", "responsable", "admin"):
            with self.subTest(role=role):
                parsed = PageToolsParser(
                    self.render_page(
                        "app_group/group_detail.html",
                        common_group=SimpleNamespace(
                            group_id=7, name="Groupe", status="open"
                        ),
                        group=SimpleNamespace(gg_id=7),
                        access_context={"can_manage_group": role != "member"},
                    )
                )
                expected = (
                    ["/groups/manage/", "/groups/7/songs/", "/groups/"]
                    if role != "member"
                    else ["/groups/"]
                )
                self.assertEqual([link["href"] for link in parsed.links], expected)
                self.assertEqual(parsed.tools_count, 1)

    def test_public_groups_tools_keep_visitor_and_member_visibility(self):
        for authenticated in (False, True):
            with self.subTest(authenticated=authenticated):
                parsed = PageToolsParser(
                    self.render_page(
                        "app_group/groups_home.html", is_authenticated=authenticated
                    )
                )
                self.assertEqual(len(parsed.links), 0 if authenticated else 1)
                if not authenticated:
                    self.assertEqual(parsed.links[0]["href"], "/login/")

    def test_dedicated_group_page_inherits_shared_tools(self):
        parsed = PageToolsParser(
            self.render_page(
                "app_group/group_functions.html",
                common_group=SimpleNamespace(group_id=7, name="Groupe"),
            )
        )
        self.assertEqual(
            [link["href"] for link in parsed.links],
            ["/groups/7/", "/groups/manage/", "/groups/7/songs/"],
        )

    def test_account_logout_confirmation_has_no_mobile_duplicate(self):
        html = self.render_page("main/connexion.html", page_mode="account")
        parsed = PageToolsParser(html)
        logout = next(link for link in parsed.links if link["href"] == "/logout/")
        self.assertEqual(logout["data-lss-logout-confirm"], "true")
        self.assertEqual(html.count('data-lss-logout-confirm="true"'), 1)
        mobile_context = html.split('class="site-panel site-mobile-side"', 1)[1].split(
            "data-mobile-actions hidden", 1
        )[0]
        self.assertNotIn('href="/logout/"', mobile_context)

    def test_legacy_mobile_action_lists_are_removed_but_context_is_kept(self):
        for name in (
            "provision_redirect",
            "provision_complete",
            "keycloak_diagnostic",
            "homepage",
        ):
            with self.subTest(page=name):
                html = self.render_page(
                    f"main/{name}.html", provision_url="https://example.org/provision"
                )
                mobile_context = html.split('class="site-panel site-mobile-side"', 1)[
                    1
                ].split("data-mobile-actions hidden", 1)[0]
                self.assertNotIn("<a ", mobile_context)
                if name == "homepage":
                    self.assertIn("site-home-mobile-hero", mobile_context)
