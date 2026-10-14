from concurrent.futures import ThreadPoolExecutor
from threading import Event
from types import SimpleNamespace
from unittest.mock import patch

from django.core import mail
from django.db import DatabaseError, IntegrityError, connections, transaction
from django.test import Client, TestCase, TransactionTestCase, override_settings
from django.urls import reverse

from app_email import services
from app_email.models import EmailNotification, EmailSettings

MEMORY_MAILERS = {
    "default": {"BACKEND": "django.core.mail.backends.locmem.EmailBackend"}
}
CONTEXT = {"subject": "Test", "name": "Alice", "message": "Test"}


@override_settings(AM_EMAIL_ENABLED=True, MAILERS=MEMORY_MAILERS)
class EmailControlTests(TestCase):
    def setUp(self):
        EmailSettings.objects.update_or_create(pk=1, defaults={"enabled": False})

    def test_both_authorizations_and_exact_block_messages(self):
        for environment, administration in (
            (False, False),
            (False, True),
            (True, False),
            (True, True),
        ):
            with self.subTest(environment=environment, administration=administration):
                services.set_email_enabled(administration)
                with override_settings(AM_EMAIL_ENABLED=environment):
                    notification = services.send_email_now(
                        "test_notification", "alice@example.test", CONTEXT
                    )
                notification.refresh_from_db()
                if not environment:
                    self.assertEqual(
                        notification.status, EmailNotification.STATUS_BLOCKED_ENV
                    )
                    self.assertEqual(
                        notification.error_message, "Impossible d'envoyer des emails"
                    )
                elif not administration:
                    self.assertEqual(
                        notification.status, EmailNotification.STATUS_BLOCKED_ADMIN
                    )
                    self.assertEqual(
                        notification.error_message,
                        "Impossible d'envoyer des emails - blocage administratif",
                    )
                else:
                    self.assertEqual(notification.status, EmailNotification.STATUS_SENT)
        self.assertEqual(len(mail.outbox), 1)

    def test_missing_settings_fail_closed_without_recreating_them(self):
        EmailSettings.objects.all().delete()
        notification = services.send_email_now(
            "test_notification", "alice@example.test", CONTEXT
        )
        self.assertEqual(notification.status, EmailNotification.STATUS_BLOCKED_ADMIN)
        self.assertFalse(EmailSettings.objects.exists())
        self.assertEqual(mail.outbox, [])

    def test_environment_block_does_not_read_admin_settings(self):
        with (
            override_settings(AM_EMAIL_ENABLED=False),
            patch(
                "app_email.services.EmailSettings.objects.using",
                side_effect=DatabaseError("Unavailable"),
            ),
        ):
            notification = services.send_email_now(
                "test_notification", "alice@example.test", CONTEXT
            )
        self.assertEqual(notification.status, EmailNotification.STATUS_BLOCKED_ENV)

    def test_settings_read_error_propagates_before_smtp(self):
        notification = services.queue_email("test_notification", "alice@example.test")
        with (
            patch(
                "app_email.services.EmailSettings.objects.using",
                side_effect=DatabaseError("Unavailable"),
            ),
            patch.object(services.EmailMultiAlternatives, "send") as send,
            self.assertRaises(DatabaseError),
        ):
            services.send_notification(notification, CONTEXT)
        send.assert_not_called()
        notification.refresh_from_db()
        self.assertEqual(notification.status, EmailNotification.STATUS_PENDING)

    def test_terminal_statuses_do_not_depend_on_global_settings(self):
        for status in (
            EmailNotification.STATUS_SENT,
            EmailNotification.STATUS_FAILED,
            EmailNotification.STATUS_SKIPPED,
            EmailNotification.STATUS_BLOCKED_ENV,
            EmailNotification.STATUS_BLOCKED_ADMIN,
            EmailNotification.STATUS_BLOCKED_ADMIN_HISTORY,
        ):
            with self.subTest(status=status):
                notification = EmailNotification.objects.create(
                    notification_type="test_notification",
                    recipient_email="alice@example.test",
                    status=status,
                )
                with patch(
                    "app_email.services.EmailSettings.objects.using",
                    side_effect=DatabaseError("Unavailable"),
                ):
                    self.assertIs(
                        services.send_notification(notification, CONTEXT), notification
                    )
                self.assertEqual(notification.status, status)
        self.assertEqual(mail.outbox, [])

    def test_blocked_notifications_are_never_retried_after_reactivation(self):
        for environment in (False, True):
            with self.subTest(environment=environment):
                services.set_email_enabled(False)
                key = f"test:blocked:{environment}"
                with override_settings(AM_EMAIL_ENABLED=environment):
                    first = services.send_email_now(
                        "test_notification",
                        "alice@example.test",
                        CONTEXT,
                        business_key=key,
                    )
                services.set_email_enabled(True)
                second = services.send_email_now(
                    "test_notification", "alice@example.test", CONTEXT, business_key=key
                )
                self.assertEqual(first.pk, second.pk)
                self.assertEqual(first.status, second.status)
        self.assertEqual(mail.outbox, [])

    def test_new_admin_period_archives_only_unchanged_current_blocks(self):
        services.set_email_enabled(True)
        services.set_email_enabled(False)
        old = services.send_email_now(
            "test_notification", "alice@example.test", CONTEXT
        )
        changed = services.send_email_now(
            "test_notification", "bob@example.test", CONTEXT
        )
        EmailNotification.objects.filter(pk=changed.pk).update(
            status=EmailNotification.STATUS_FAILED
        )
        with override_settings(AM_EMAIL_ENABLED=False):
            environmental = services.send_email_now(
                "test_notification", "eve@example.test", CONTEXT
            )
        services.set_email_enabled(False)
        old.refresh_from_db()
        self.assertEqual(old.status, EmailNotification.STATUS_BLOCKED_ADMIN)
        services.set_email_enabled(True)
        old.refresh_from_db()
        self.assertEqual(old.status, EmailNotification.STATUS_BLOCKED_ADMIN)
        services.set_email_enabled(False)
        old.refresh_from_db()
        changed.refresh_from_db()
        environmental.refresh_from_db()
        self.assertEqual(old.status, EmailNotification.STATUS_BLOCKED_ADMIN_HISTORY)
        self.assertEqual(
            old.error_message, "Impossible d'envoyer des emails - blocage administratif"
        )
        self.assertEqual(changed.status, EmailNotification.STATUS_FAILED)
        self.assertEqual(environmental.status, EmailNotification.STATUS_BLOCKED_ENV)
        current = services.send_email_now(
            "test_notification", "alice@example.test", CONTEXT
        )
        self.assertEqual(
            list(
                EmailNotification.objects.filter(
                    status=EmailNotification.STATUS_BLOCKED_ADMIN
                )
            ),
            [current],
        )
        services.set_email_enabled(False)
        current.refresh_from_db()
        self.assertEqual(current.status, EmailNotification.STATUS_BLOCKED_ADMIN)

    def test_archive_and_setting_are_rolled_back_together(self):
        services.set_email_enabled(True)
        old = EmailNotification.objects.create(
            notification_type="test_notification",
            recipient_email="alice@example.test",
            status=EmailNotification.STATUS_BLOCKED_ADMIN,
        )
        with (
            patch.object(
                EmailSettings, "save", side_effect=DatabaseError("Unavailable")
            ),
            self.assertRaises(DatabaseError),
        ):
            services.set_email_enabled(False)
        old.refresh_from_db()
        self.assertEqual(old.status, EmailNotification.STATUS_BLOCKED_ADMIN)
        self.assertTrue(services.get_email_settings().enabled)

    def test_settings_are_a_singleton(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            EmailSettings.objects.create(pk=2)

    @override_settings(
        DEFAULT_FROM_EMAIL="no-reply@animation-messe.fr",
        AM_EMAIL_PLANNING_FROM_EMAIL="planning-noreply@animation-messe.fr",
    )
    def test_sender_profile_is_persisted_and_reused(self):
        services.set_email_enabled(True)
        for sender, address in (
            ("default", "no-reply@animation-messe.fr"),
            ("planning", "planning-noreply@animation-messe.fr"),
        ):
            with self.subTest(sender=sender):
                key = f"test:sender:{sender}"
                first = services.send_email_now(
                    "test_notification",
                    "alice@example.test",
                    CONTEXT,
                    sender_key=sender,
                    business_key=key,
                )
                self.assertEqual(
                    mail.outbox[-1].message()["From"].addresses[0].addr_spec, address
                )
                second = services.queue_email(
                    "test_notification",
                    "bob@example.test",
                    sender_key="default",
                    business_key=key,
                )
                self.assertEqual(first.pk, second.pk)
                self.assertEqual(second.sender_key, sender)
                self.assertEqual(second.recipient_email, "alice@example.test")
        self.assertEqual(len(mail.outbox), 2)

    def test_unknown_sender_is_rejected_before_creation(self):
        with self.assertRaises(ValueError):
            services.queue_email(
                "test_notification", "alice@example.test", sender_key="unknown"
            )
        self.assertFalse(EmailNotification.objects.exists())


@override_settings(AM_EMAIL_ENABLED=True, MAILERS=MEMORY_MAILERS)
class ConcurrentAdminBlockTests(TransactionTestCase):
    def test_new_attempt_waits_for_admin_archiving(self):
        keys = ("test:admin-period:old", "test:admin-period:new")
        self.addCleanup(EmailNotification.objects.filter(business_key__in=keys).delete)
        services.set_email_enabled(True)
        old = EmailNotification.objects.create(
            notification_type="test_notification",
            recipient_email="alice@example.test",
            status=EmailNotification.STATUS_BLOCKED_ADMIN,
            business_key=keys[0],
        )
        locked, release, started = Event(), Event(), Event()

        def block():
            try:
                with transaction.atomic():
                    services.set_email_enabled(False)
                    locked.set()
                    if not release.wait(5):
                        raise TimeoutError("Admin update not released")
            finally:
                connections.close_all()

        def attempt():
            try:
                notification = services.queue_email(
                    "test_notification", "bob@example.test", business_key=keys[1]
                )
                started.set()
                return services.send_notification(notification, CONTEXT)
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=2) as executor:
            admin = executor.submit(block)
            try:
                self.assertTrue(locked.wait(5))
                sender = executor.submit(attempt)
                self.assertTrue(started.wait(5))
            finally:
                release.set()
            admin.result(5)
            new = sender.result(5)
        old.refresh_from_db()
        self.assertEqual(old.status, EmailNotification.STATUS_BLOCKED_ADMIN_HISTORY)
        self.assertEqual(new.status, EmailNotification.STATUS_BLOCKED_ADMIN)
        self.assertEqual(mail.outbox, [])


@override_settings(AM_EMAIL_ENABLED=False)
class EmailSettingsPageTests(TestCase):
    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)
        self.user = SimpleNamespace(
            is_authenticated=True, is_admin=True, username="admin"
        )
        self.enterContext(
            patch("app_main.middleware.refresh_request_user", return_value=self.user)
        )
        self.url = reverse("site_params")

    def test_global_form_is_independent_of_language_and_server_authorization(self):
        for language in ("fr", "en"):
            page = self.client.get(self.url, {"language": language})
            self.assertEqual(page.status_code, 200)
            self.assertContains(page, 'name="action" value="save_email_settings"')
        token = self.client.cookies["csrftoken"].value
        response = self.client.post(
            f"{self.url}?language=en",
            {
                "csrfmiddlewaretoken": token,
                "action": "save_email_settings",
                "email-settings-enabled": "on",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(services.get_email_settings().enabled)
        page = self.client.get(self.url, {"language": "fr"})
        self.assertTrue(page.context["email_admin_enabled"])
        self.assertFalse(page.context["email_environment_enabled"])
        self.assertContains(page, "Impossible d'envoyer des emails", html=False)

    def test_global_form_is_csrf_protected(self):
        response = self.client.post(
            self.url, {"action": "save_email_settings", "email-settings-enabled": "on"}
        )
        self.assertEqual(response.status_code, 403)
        self.assertFalse(services.get_email_settings().enabled)

    @override_settings(AM_EMAIL_ENABLED=True)
    def test_page_shows_explicit_admin_block_message(self):
        services.set_email_enabled(False)
        page = self.client.get(self.url)
        self.assertContains(
            page, "Impossible d'envoyer des emails - blocage administratif"
        )

    def test_only_site_admins_can_change_global_authorization(self):
        self.user.is_admin = False
        self.assertEqual(self.client.get(self.url).status_code, 404)
        self.user.is_authenticated = False
        self.assertEqual(self.client.get(self.url).status_code, 302)
