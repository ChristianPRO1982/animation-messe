from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.core import mail
from django.test import SimpleTestCase, override_settings
from django.utils import timezone

from app_notification.models import EmailNotification
from app_notification.services import email as email_service


def build_notification(**overrides):
    values = {
        "pk": 1,
        "status": EmailNotification.STATUS_PENDING,
        "notification_type": "am_member_invitation",
        "recipient": "alice@example.test",
        "provider_message_id": "",
        "error_message": "",
        "sent_at": None,
        "save": Mock(),
    }
    values.update(overrides)
    return SimpleNamespace(**values)


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    EMAIL_ENABLED=True,
    DEFAULT_FROM_EMAIL="no-reply@example.test",
    EMAIL_FROM_DISPLAY="Animation Messe <no-reply@example.test>",
)
class EmailNotificationServiceTests(SimpleTestCase):
    def test_create_notification_builds_pending_trace(self):
        notification = build_notification()

        with patch.object(
            email_service.EmailNotification.objects,
            "get_or_create",
            return_value=(notification, True),
        ) as get_or_create:
            result, created = email_service.create_notification(
                notification_type="am_member_invitation",
                recipient="alice@example.test",
                group_id=7,
                object_type="am_member_request",
                object_id=12,
                idempotency_key="am_member_invitation|12|alice@example.test",
            )

        self.assertIs(result, notification)
        self.assertTrue(created)
        get_or_create.assert_called_once()
        defaults = get_or_create.call_args.kwargs["defaults"]
        self.assertEqual(defaults["recipient"], "alice@example.test")
        self.assertEqual(defaults["group_id"], 7)

    def test_send_transactional_email_uses_templates_and_marks_sent(self):
        notification = build_notification()

        with patch(
            "app_notification.services.email.create_notification",
            return_value=(notification, True),
        ):
            result = email_service.send_transactional_email(
                notification_type="am_member_invitation",
                recipient="alice@example.test",
                group_id=7,
                object_type="am_member_request",
                object_id=12,
                idempotency_key="am_member_invitation|12|alice@example.test",
                context={
                    "first_name": "Alice",
                    "last_name": "Martin",
                    "group_name": "Chorale",
                    "invitation_url": "https://example.test/invitation/token",
                    "expires_at": timezone.now() + timezone.timedelta(days=14),
                },
            )

        self.assertIs(result, notification)
        self.assertEqual(notification.status, EmailNotification.STATUS_SENT)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["alice@example.test"])
        self.assertEqual(mail.outbox[0].subject, "Invitation Animation Messe")
        self.assertIn("Chorale", mail.outbox[0].body)
        self.assertNotIn("token-public", str(notification.__dict__))
        notification.save.assert_called_once()

    def test_idempotency_prevents_duplicate_send_when_already_sent(self):
        notification = build_notification(status=EmailNotification.STATUS_SENT)

        with patch(
            "app_notification.services.email.create_notification",
            return_value=(notification, False),
        ):
            result = email_service.send_transactional_email(
                notification_type="am_member_invitation",
                recipient="alice@example.test",
                context={},
                object_type="am_member_request",
                object_id=12,
                idempotency_key="same-key",
            )

        self.assertIs(result, notification)
        self.assertEqual(len(mail.outbox), 0)
        notification.save.assert_not_called()

    @patch("app_notification.services.email.get_connection")
    def test_backend_error_marks_notification_failed(self, get_connection):
        get_connection.side_effect = RuntimeError("SMTP unavailable")
        notification = build_notification()

        with self.assertLogs("app_notification.services.email", level="ERROR"):
            result = email_service.send_notification(
                notification,
                subject="Sujet",
                body_text="Corps",
            )

        self.assertIs(result, notification)
        self.assertEqual(notification.status, EmailNotification.STATUS_FAILED)
        self.assertIn("SMTP unavailable", notification.error_message)
        self.assertEqual(len(mail.outbox), 0)
        notification.save.assert_called_once()


@override_settings(EMAIL_ENABLED=False)
class EmailNotificationDisabledTests(SimpleTestCase):
    def test_disabled_email_backend_does_not_send_real_message(self):
        notification = build_notification()

        result = email_service.send_notification(
            notification,
            subject="Sujet",
            body_text="Corps",
        )

        self.assertIs(result, notification)
        self.assertEqual(notification.status, EmailNotification.STATUS_SENT)
        self.assertEqual(notification.provider_message_id, "email-disabled")
        self.assertEqual(len(mail.outbox), 0)
        notification.save.assert_called_once()
