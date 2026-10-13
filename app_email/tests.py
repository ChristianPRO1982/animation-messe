from datetime import timedelta
from unittest.mock import Mock, patch

from django.core import mail
from django.core.mail.backends.base import BaseEmailBackend
from django.test import RequestFactory, SimpleTestCase, override_settings
from django.utils import timezone

from app_email import services
from app_email.admin import EmailNotificationAdmin
from app_email.models import EmailNotification
from app_main.middleware import SessionUserMiddleware


class FailingEmailBackend(BaseEmailBackend):
    def send_messages(self, email_messages):
        raise RuntimeError("token=secret password=hidden")


class EmailNotificationModelTests(SimpleTestCase):
    def test_notification_defaults_to_pending(self):
        notification = EmailNotification(
            notification_type="test_notification",
            recipient_email="alice@example.test",
        )

        self.assertEqual(notification.status, EmailNotification.STATUS_PENDING)
        self.assertIsNone(notification.business_key)

    def test_business_key_is_unique_when_present(self):
        field = EmailNotification._meta.get_field("business_key")

        self.assertTrue(field.unique)
        self.assertTrue(field.null)
        self.assertTrue(field.blank)

    def test_status_transitions_update_dates(self):
        notification = EmailNotification(
            notification_type="test_notification",
            recipient_email="alice@example.test",
        )
        notification.save = Mock()
        sent_at = timezone.now()
        failed_at = sent_at + timedelta(minutes=1)
        skipped_at = sent_at + timedelta(minutes=2)

        notification.mark_sent(provider_message_id="provider-1", now=sent_at)
        self.assertEqual(notification.status, EmailNotification.STATUS_SENT)
        self.assertEqual(notification.provider_message_id, "provider-1")
        self.assertEqual(notification.sent_at, sent_at)
        self.assertIsNone(notification.failed_at)

        notification.mark_failed("erreur", now=failed_at)
        self.assertEqual(notification.status, EmailNotification.STATUS_FAILED)
        self.assertEqual(notification.error_message, "erreur")
        self.assertEqual(notification.failed_at, failed_at)

        notification.mark_skipped("désactivé", now=skipped_at)
        self.assertEqual(notification.status, EmailNotification.STATUS_SKIPPED)
        self.assertEqual(notification.error_message, "désactivé")
        self.assertEqual(notification.failed_at, skipped_at)
        self.assertEqual(notification.save.call_count, 3)


@override_settings(
    MAILERS={
        "default": {
            "BACKEND": "django.core.mail.backends.locmem.EmailBackend",
        }
    },
    DEFAULT_FROM_EMAIL="no-reply@example.test",
    AM_EMAIL_FROM_NAME="Animation Messe",
    AM_EMAIL_SUBJECT_PREFIX="",
)
class EmailServiceTests(SimpleTestCase):
    def setUp(self):
        if hasattr(mail, "outbox"):
            mail.outbox.clear()

    @patch("app_email.services.EmailNotification")
    def test_queue_email_creates_notification(self, notification_model):
        created = object()
        notification_model.objects.create.return_value = created

        notification = services.queue_email(
            "test_notification",
            "alice@example.test",
            recipient_member_id="11111111-1111-1111-1111-111111111111",
        )

        self.assertIs(notification, created)
        notification_model.objects.create.assert_called_once_with(
            notification_type="test_notification",
            business_key=None,
            recipient_email="alice@example.test",
            recipient_member_id="11111111-1111-1111-1111-111111111111",
            group_id=None,
            content_object_type="",
            content_object_id="",
        )

    @patch("app_email.services.EmailNotification")
    def test_queue_email_reuses_business_key(self, notification_model):
        existing = object()
        notification_model.objects.get_or_create.return_value = (existing, False)

        with patch("app_email.services.transaction.atomic") as atomic:
            atomic.return_value.__enter__ = Mock(return_value=None)
            atomic.return_value.__exit__ = Mock(return_value=False)
            notification = services.queue_email(
                "test_notification",
                "alice.changed@example.test",
                business_key="test:key:reuse",
            )

        self.assertIs(notification, existing)
        notification_model.objects.get_or_create.assert_called_once()
        call_kwargs = notification_model.objects.get_or_create.call_args.kwargs
        self.assertEqual(call_kwargs["business_key"], "test:key:reuse")
        self.assertEqual(
            call_kwargs["defaults"]["recipient_email"],
            "alice.changed@example.test",
        )

    @override_settings(AM_EMAIL_SUBJECT_PREFIX="[AM] ")
    def test_render_email_uses_templates_and_normalizes_subject(self):
        rendered = services.render_email(
            "test_notification",
            {
                "subject": "Sujet\n  test",
                "name": "Alice",
                "message": "Bienvenue",
            },
        )

        self.assertEqual(rendered.subject, "[AM] Sujet test")
        self.assertIn("Bonjour Alice", rendered.body_text)
        self.assertIn("<p>Bienvenue</p>", rendered.body_html)

    @override_settings(AM_EMAIL_ENABLED=True)
    def test_send_notification_sends_with_memory_backend(self):
        notification = EmailNotification(
            notification_type="test_notification",
            recipient_email="alice@example.test",
        )
        notification.save = Mock()

        services.send_notification(
            notification,
            {
                "subject": "Invitation",
                "name": "Alice",
                "message": "Bienvenue",
            },
        )

        self.assertEqual(notification.status, EmailNotification.STATUS_SENT)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["alice@example.test"])
        self.assertEqual(mail.outbox[0].subject, "Invitation")
        self.assertEqual(
            mail.outbox[0].from_email,
            "Animation Messe <no-reply@example.test>",
        )
        self.assertTrue(mail.outbox[0].alternatives)

    @override_settings(
        AM_EMAIL_ENABLED=True,
        MAILERS={
            "default": {
                "BACKEND": "app_email.tests.FailingEmailBackend",
            }
        },
    )
    def test_send_notification_marks_failed_on_backend_error(self):
        notification = EmailNotification(
            notification_type="test_notification",
            recipient_email="alice@example.test",
        )
        notification.save = Mock()

        services.send_notification(
            notification,
            {
                "subject": "Invitation",
                "name": "Alice",
                "message": "Bienvenue",
            },
        )

        self.assertEqual(notification.status, EmailNotification.STATUS_FAILED)
        self.assertIn("token=***", notification.error_message)
        self.assertIn("password=***", notification.error_message)
        self.assertNotIn("secret", notification.error_message)
        self.assertNotIn("hidden", notification.error_message)

    @override_settings(AM_EMAIL_ENABLED=False)
    def test_send_notification_skips_when_email_is_disabled(self):
        notification = EmailNotification(
            notification_type="test_notification",
            recipient_email="alice@example.test",
        )
        notification.save = Mock()

        services.send_notification(
            notification,
            {
                "subject": "Invitation",
                "name": "Alice",
                "message": "Bienvenue",
            },
        )

        self.assertEqual(notification.status, EmailNotification.STATUS_SKIPPED)
        self.assertEqual(getattr(mail, "outbox", []), [])

    @patch("app_email.services.send_notification")
    @patch("app_email.services.queue_email")
    def test_send_email_now_queues_then_sends(self, queue_email, send_notification):
        notification = object()
        queue_email.return_value = notification
        send_notification.return_value = notification
        context = {"subject": "Invitation"}

        result = services.send_email_now(
            "test_notification",
            "alice@example.test",
            context,
            business_key="test:key:now",
        )

        self.assertIs(result, notification)
        queue_email.assert_called_once_with(
            "test_notification",
            "alice@example.test",
            context,
            recipient_member_id=None,
            group=None,
            content_object=None,
            business_key="test:key:now",
        )
        send_notification.assert_called_once_with(notification, context)


class EmailAdminTests(SimpleTestCase):
    def test_admin_exposes_readonly_trace_fields(self):
        admin_view = EmailNotificationAdmin(EmailNotification, None)

        self.assertIn("notification_type", admin_view.list_display)
        self.assertIn("status", admin_view.list_filter)
        self.assertIn("business_key", admin_view.readonly_fields)
        self.assertFalse(admin_view.has_add_permission(None))
        self.assertFalse(admin_view.has_change_permission(None))


class AdminMiddlewareTests(SimpleTestCase):
    def test_session_user_middleware_keeps_admin_user(self):
        factory = RequestFactory()
        request = factory.get("/admin/")
        request.session = {}
        request.user = object()
        original_user = request.user

        response = SessionUserMiddleware(lambda req: req)(request)

        self.assertIs(response.user, original_user)

