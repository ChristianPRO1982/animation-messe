from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Event
from traceback import format_exception
from unittest.mock import Mock, patch

from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.core import mail
from django.core.mail.backends.base import BaseEmailBackend
from django.db import DatabaseError, IntegrityError, close_old_connections, connections
from django.template import TemplateDoesNotExist
from django.test import (
    RequestFactory,
    SimpleTestCase,
    TestCase,
    TransactionTestCase,
    override_settings,
)
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
class EmailServiceTests(TestCase):
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

    @override_settings(AM_EMAIL_ENABLED=True, AM_EMAIL_SUBJECT_PREFIX="[AM]\r\n  ")
    def test_subject_prefix_is_normalized_without_duplicate_prefix(self):
        for subject in ("Sujet", "[AM] Sujet"):
            with self.subTest(subject=subject):
                notification = services.send_email_now(
                    "test_notification",
                    "alice@example.test",
                    {"subject": subject, "message": "Test"},
                )
                notification.refresh_from_db()
                self.assertEqual(notification.status, EmailNotification.STATUS_SENT)
                self.assertEqual(mail.outbox[-1].subject, "[AM] Sujet")

    def test_text_templates_preserve_characters_while_html_remains_escaped(self):
        context = {
            "subject": "A & B : O'Neil",
            "name": "Alice & Bob",
            "message": '<script>alert("Test")</script> & suite',
        }
        rendered = services.render_email("test_notification", context)

        self.assertEqual(rendered.subject, context["subject"])
        self.assertIn("Bonjour Alice & Bob", rendered.body_text)
        self.assertIn(context["message"], rendered.body_text)
        self.assertIn("Bonjour Alice &amp; Bob", rendered.body_html)
        self.assertIn("&lt;script&gt;", rendered.body_html)
        self.assertNotIn(context["message"], rendered.body_html)
        self.assertNotIn("<script>", rendered.body_html)

    @override_settings(AM_EMAIL_ENABLED=True)
    def test_optional_html_is_absent_only_when_template_is_missing(self):
        templates = {
            "emails/test_notification/subject.txt": "Test",
            "emails/test_notification/body.txt": "Message texte",
        }
        template_settings = [
            {
                "BACKEND": "django.template.backends.django.DjangoTemplates",
                "OPTIONS": {
                    "loaders": [("django.template.loaders.locmem.Loader", templates)],
                },
            }
        ]
        with override_settings(TEMPLATES=template_settings):
            notification = services.send_email_now(
                "test_notification", "alice@example.test", {}
            )
        notification.refresh_from_db()
        self.assertEqual(notification.status, EmailNotification.STATUS_SENT)
        self.assertEqual(mail.outbox[0].body, "Message texte")
        self.assertEqual(mail.outbox[0].alternatives, [])

        templates["emails/test_notification/body.html"] = (
            '{% include "missing_fragment.html" %}'
        )
        with override_settings(TEMPLATES=template_settings):
            with self.assertRaises(TemplateDoesNotExist):
                services.render_email("test_notification", {})
            with self.assertLogs("app_email", level="ERROR"):
                notification = services.send_email_now(
                    "test_notification", "alice@example.test", {}
                )
        notification.refresh_from_db()
        self.assertEqual(notification.status, EmailNotification.STATUS_FAILED)
        self.assertEqual(notification.error_message, "Template email introuvable.")
        self.assertEqual(len(mail.outbox), 1)

    @override_settings(AM_EMAIL_ENABLED=True)
    def test_send_notification_sends_with_memory_backend(self):
        notification = EmailNotification.objects.create(
            notification_type="test_notification",
            recipient_email="alice@example.test",
        )

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

    @override_settings(AM_EMAIL_ENABLED=True)
    def test_sender_display_name_is_preserved_as_a_single_address(self):
        names = ("Equipe, AM", 'Equipe "AM"', "Equipe: AM", "Équipe AM")
        for name in names:
            with self.subTest(name=name), override_settings(AM_EMAIL_FROM_NAME=name):
                notification = services.send_email_now(
                    "test_notification",
                    "alice@example.test",
                    {"subject": "Test", "message": "Test"},
                )
                notification.refresh_from_db()
                self.assertEqual(notification.status, EmailNotification.STATUS_SENT)
                addresses = mail.outbox[-1].message()["From"].addresses
                self.assertEqual(len(addresses), 1)
                self.assertEqual(addresses[0].display_name, name)
                self.assertEqual(addresses[0].addr_spec, "no-reply@example.test")

    @override_settings(AM_EMAIL_ENABLED=True)
    def test_zero_backend_result_is_failed_and_not_retried(self):
        with patch.object(
            services.EmailMultiAlternatives, "send", return_value=0
        ) as send:
            first = services.send_email_now(
                "test_notification",
                "alice@example.test",
                {"subject": "Test", "message": "Test"},
                business_key="test:backend-zero",
            )
            second = services.send_email_now(
                "test_notification",
                "alice@example.test",
                {"subject": "Test", "message": "Test"},
                business_key="test:backend-zero",
            )
        first.refresh_from_db()
        self.assertEqual(first.pk, second.pk)
        self.assertEqual(first.status, EmailNotification.STATUS_FAILED)
        self.assertEqual(second.status, EmailNotification.STATUS_FAILED)
        self.assertEqual(
            first.error_message, "Le backend email n'a envoyé aucun message."
        )
        self.assertEqual(EmailNotification.objects.count(), 1)
        self.assertEqual(send.call_count, 1)
        self.assertEqual(mail.outbox, [])

    @override_settings(
        AM_EMAIL_ENABLED=True,
        MAILERS={
            "default": {
                "BACKEND": "app_email.tests.FailingEmailBackend",
            }
        },
    )
    def test_send_notification_marks_failed_on_backend_error(self):
        notification = EmailNotification.objects.create(
            notification_type="test_notification",
            recipient_email="alice@example.test",
        )

        with self.assertLogs("app_email", level="ERROR") as logs:
            services.send_notification(
                notification,
                {
                    "subject": "Invitation",
                    "name": "Alice",
                    "message": "Bienvenue",
                },
            )

        self.assertEqual(notification.status, EmailNotification.STATUS_FAILED)
        self.assertEqual(
            notification.error_message, "Echec technique de l'envoi email."
        )
        self.assertNotIn("secret", notification.error_message)
        self.assertNotIn("hidden", notification.error_message)
        log_output = "\n".join(logs.output)
        self.assertIn(notification.error_message, log_output)
        self.assertNotIn("secret", log_output)
        self.assertNotIn("hidden", log_output)

    @override_settings(AM_EMAIL_ENABLED=True)
    def test_backend_error_contents_are_never_stored_or_logged(self):
        errors = (
            "token = sensitive_value",
            "Authorization: Bearer sensitive_value",
            '{"password": "sensitive_value"}',
            "password='sensitive_value with spaces'",
            "Unstructured backend response: sensitive_value",
        )
        for error in errors:
            with self.subTest(error=error):
                notification = EmailNotification.objects.create(
                    notification_type="test_notification",
                    recipient_email="alice@example.test",
                )
                with (
                    patch.object(
                        services.EmailMultiAlternatives,
                        "send",
                        side_effect=RuntimeError(error),
                    ),
                    self.assertLogs("app_email", level="ERROR") as logs,
                ):
                    services.send_notification(
                        notification, {"subject": "Test", "message": "Test"}
                    )

                self.assertEqual(notification.status, EmailNotification.STATUS_FAILED)
                self.assertNotIn("sensitive_value", notification.error_message)
                self.assertNotIn("sensitive_value", "\n".join(logs.output))
                for record in logs.records:
                    self.assertIsNone(record.exc_info)
                    self.assertIsNone(record.stack_info)

    @override_settings(AM_EMAIL_ENABLED=True)
    def test_persistence_error_does_not_chain_sensitive_backend_error(self):
        notification = services.queue_email("test_notification", "alice@example.test")
        with (
            patch.object(
                services.EmailMultiAlternatives,
                "send",
                side_effect=RuntimeError("token=sensitive_value"),
            ),
            patch.object(
                notification,
                "mark_failed",
                side_effect=DatabaseError("Persistence unavailable"),
            ),
            self.assertLogs("app_email", level="ERROR") as logs,
            self.assertRaises(DatabaseError) as caught,
        ):
            services.send_notification(notification, {"subject": "Test"})

        self.assertIsNone(caught.exception.__context__)
        self.assertNotIn("sensitive_value", "".join(format_exception(caught.exception)))
        self.assertNotIn("sensitive_value", "\n".join(logs.output))
        self.assertIn("Echec technique de l'envoi email.", "\n".join(logs.output))
        self.assertTrue(all(record.exc_info is None for record in logs.records))
        notification.refresh_from_db()
        self.assertEqual(notification.status, EmailNotification.STATUS_PENDING)
        self.assertEqual(mail.outbox, [])

    @override_settings(AM_EMAIL_ENABLED=True)
    def test_sent_status_persistence_error_is_not_a_backend_failure(self):
        notification = services.queue_email("test_notification", "alice@example.test")
        with (
            patch.object(
                notification,
                "mark_sent",
                side_effect=DatabaseError("Persistence unavailable"),
            ),
            patch.object(notification, "mark_failed") as mark_failed,
            self.assertRaises(DatabaseError),
        ):
            services.send_notification(notification, {"subject": "Test"})

        mark_failed.assert_not_called()
        self.assertEqual(len(mail.outbox), 1)
        notification.refresh_from_db()
        self.assertEqual(notification.status, EmailNotification.STATUS_PENDING)

    @override_settings(AM_EMAIL_ENABLED=True)
    def test_send_notification_ignores_non_pending_notifications(self):
        for status in (
            EmailNotification.STATUS_SENT,
            EmailNotification.STATUS_FAILED,
            EmailNotification.STATUS_SKIPPED,
        ):
            with self.subTest(status=status):
                notification = EmailNotification.objects.create(
                    notification_type="test_notification",
                    recipient_email="alice@example.test",
                    status=status,
                )
                updated_at = notification.updated_at
                mail.outbox.clear()

                result = services.send_notification(
                    notification,
                    {
                        "subject": "Invitation",
                        "name": "Alice",
                        "message": "Bienvenue",
                    },
                )

                self.assertIs(result, notification)
                self.assertEqual(notification.status, status)
                self.assertEqual(mail.outbox, [])
                notification.refresh_from_db()
                self.assertEqual(notification.status, status)
                self.assertEqual(notification.updated_at, updated_at)

    @override_settings(AM_EMAIL_ENABLED=False)
    def test_send_notification_skips_when_email_is_disabled(self):
        notification = EmailNotification.objects.create(
            notification_type="test_notification",
            recipient_email="alice@example.test",
        )

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

    @override_settings(AM_EMAIL_ENABLED=True)
    @patch("app_email.services.queue_email")
    def test_send_email_now_does_not_resend_existing_sent_notification(
        self, queue_email
    ):
        notification = EmailNotification.objects.create(
            notification_type="test_notification",
            recipient_email="alice@example.test",
            business_key="test:key:now",
            status=EmailNotification.STATUS_SENT,
        )
        updated_at = notification.updated_at
        queue_email.return_value = notification

        result = services.send_email_now(
            "test_notification",
            "alice@example.test",
            {
                "subject": "Invitation",
                "name": "Alice",
                "message": "Bienvenue",
            },
            business_key="test:key:now",
        )

        self.assertIs(result, notification)
        self.assertEqual(mail.outbox, [])
        notification.refresh_from_db()
        self.assertEqual(notification.updated_at, updated_at)

    @override_settings(AM_EMAIL_ENABLED=True)
    @patch("app_email.services.queue_email")
    def test_send_email_now_does_not_retry_existing_failed_notification(
        self, queue_email
    ):
        notification = EmailNotification.objects.create(
            notification_type="test_notification",
            recipient_email="alice@example.test",
            business_key="test:key:failed",
            status=EmailNotification.STATUS_FAILED,
            error_message="erreur precedente",
        )
        updated_at = notification.updated_at
        queue_email.return_value = notification

        result = services.send_email_now(
            "test_notification",
            "alice@example.test",
            {
                "subject": "Invitation",
                "name": "Alice",
                "message": "Bienvenue",
            },
            business_key="test:key:failed",
        )

        self.assertIs(result, notification)
        self.assertEqual(notification.status, EmailNotification.STATUS_FAILED)
        self.assertEqual(mail.outbox, [])
        notification.refresh_from_db()
        self.assertEqual(notification.error_message, "erreur precedente")
        self.assertEqual(notification.updated_at, updated_at)

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


@override_settings(
    AM_EMAIL_ENABLED=True,
    MAILERS={
        "default": {
            "BACKEND": "django.core.mail.backends.locmem.EmailBackend",
        }
    },
    DEFAULT_FROM_EMAIL="no-reply@example.test",
)
class EmailServiceIntegrationTests(TestCase):
    def test_stale_pending_instance_does_not_resend(self):
        first = services.queue_email(
            "test_notification", "alice@example.test", business_key="test:stale"
        )
        stale = EmailNotification.objects.get(pk=first.pk)
        context = {"subject": "Test", "name": "Alice", "message": "Test"}

        services.send_notification(first, context)
        result = services.send_notification(stale, context)

        self.assertIs(result, stale)
        self.assertEqual(stale.status, EmailNotification.STATUS_SENT)
        self.assertEqual(EmailNotification.objects.count(), 1)
        self.assertEqual(len(mail.outbox), 1)

    def test_same_business_key_sends_only_once(self):
        context = {"subject": "Invitation", "name": "Alice", "message": "Bienvenue"}

        first = services.send_email_now(
            "test_notification",
            "alice@example.test",
            context,
            business_key="test:integration:sent",
        )
        second = services.send_email_now(
            "test_notification",
            "alice@example.test",
            context,
            business_key="test:integration:sent",
        )

        self.assertEqual(first.pk, second.pk)
        self.assertEqual(EmailNotification.objects.count(), 1)
        first.refresh_from_db()
        self.assertEqual(first.status, EmailNotification.STATUS_SENT)
        self.assertEqual(second.status, EmailNotification.STATUS_SENT)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["alice@example.test"])

    def test_existing_failed_notification_is_not_retried(self):
        existing = EmailNotification.objects.create(
            notification_type="test_notification",
            recipient_email="alice@example.test",
            business_key="test:integration:failed",
            status=EmailNotification.STATUS_FAILED,
            error_message="erreur precedente",
            failed_at=timezone.now(),
        )
        failed_at = existing.failed_at
        updated_at = existing.updated_at

        result = services.send_email_now(
            "test_notification",
            "alice@example.test",
            {"subject": "Invitation", "name": "Alice", "message": "Bienvenue"},
            business_key="test:integration:failed",
        )

        self.assertEqual(result.pk, existing.pk)
        self.assertEqual(result.status, EmailNotification.STATUS_FAILED)
        self.assertEqual(EmailNotification.objects.count(), 1)
        existing.refresh_from_db()
        self.assertEqual(existing.status, EmailNotification.STATUS_FAILED)
        self.assertEqual(existing.error_message, "erreur precedente")
        self.assertEqual(existing.failed_at, failed_at)
        self.assertEqual(existing.updated_at, updated_at)
        self.assertEqual(mail.outbox, [])


@override_settings(
    AM_EMAIL_ENABLED=True,
    MAILERS={"default": {"BACKEND": "django.core.mail.backends.locmem.EmailBackend"}},
    DEFAULT_FROM_EMAIL="no-reply@example.test",
)
class EmailConcurrentDeliveryTests(TransactionTestCase):
    def test_concurrent_pending_instances_send_only_once(self):
        first = services.queue_email(
            "test_notification", "alice@example.test", business_key="test:concurrent"
        )
        second = EmailNotification.objects.get(pk=first.pk)
        sending = Event()
        release = Event()
        second_started = Event()
        original_send = services.EmailMultiAlternatives.send

        def delayed_send(message, *args, **kwargs):
            sending.set()
            if not release.wait(timeout=5):
                raise TimeoutError("Test did not release the first sender")
            return original_send(message, *args, **kwargs)

        def deliver(notification, started=None):
            close_old_connections()
            try:
                if started is not None:
                    started.set()
                return services.send_notification(
                    notification, {"subject": "Test", "message": "Test"}
                ).status
            finally:
                connections.close_all()

        with (
            patch.object(
                services.EmailMultiAlternatives,
                "send",
                autospec=True,
                side_effect=delayed_send,
            ) as send,
            ThreadPoolExecutor(max_workers=2) as executor,
        ):
            first_result = executor.submit(deliver, first)
            try:
                self.assertTrue(sending.wait(timeout=5))
                second_result = executor.submit(deliver, second, second_started)
                self.assertTrue(second_started.wait(timeout=5))
            finally:
                release.set()
            self.assertEqual(
                first_result.result(timeout=5), EmailNotification.STATUS_SENT
            )
            self.assertEqual(
                second_result.result(timeout=5), EmailNotification.STATUS_SENT
            )
            self.assertEqual(send.call_count, 1)

        first.refresh_from_db()
        self.assertEqual(first.status, EmailNotification.STATUS_SENT)
        self.assertEqual(EmailNotification.objects.count(), 1)
        self.assertEqual(len(mail.outbox), 1)


class EmailQueueIntegrityTests(TransactionTestCase):
    def test_invalid_group_preserves_integrity_error(self):
        business_key = "test:invalid-group"
        with self.assertRaises(IntegrityError):
            services.queue_email(
                "test_notification",
                "alice@example.test",
                group=-1,
                business_key=business_key,
            )
        self.assertFalse(
            EmailNotification.objects.filter(business_key=business_key).exists()
        )


class UnsavedEmailNotificationTests(SimpleTestCase):
    @override_settings(AM_EMAIL_ENABLED=True)
    def test_unsaved_notification_is_rejected_before_rendering_or_sending(self):
        for primary_key in (None, 123):
            with self.subTest(primary_key=primary_key):
                notification = EmailNotification(
                    pk=primary_key,
                    notification_type="test_notification",
                    recipient_email="alice@example.test",
                )
                with (
                    patch("app_email.services.render_email") as render,
                    patch.object(services.EmailMultiAlternatives, "send") as send,
                    self.assertRaisesMessage(ValueError, "enregistree avant l'envoi"),
                ):
                    services.send_notification(notification, {"subject": "Test"})

                render.assert_not_called()
                send.assert_not_called()
                self.assertTrue(notification._state.adding)
                self.assertEqual(notification.status, EmailNotification.STATUS_PENDING)


class EmailAdminTests(SimpleTestCase):
    def test_admin_exposes_readonly_trace_fields(self):
        admin_view = EmailNotificationAdmin(EmailNotification, None)

        self.assertIn("notification_type", admin_view.list_display)
        self.assertIn("status", admin_view.list_filter)
        self.assertIn("business_key", admin_view.readonly_fields)
        self.assertFalse(admin_view.has_add_permission(None))
        self.assertFalse(admin_view.has_change_permission(None))

    def test_admin_disallows_deletion_even_for_superusers(self):
        admin_view = EmailNotificationAdmin(EmailNotification, AdminSite())
        request = RequestFactory().get("/admin/app_email/emailnotification/")
        request.user = get_user_model()(
            is_active=True, is_staff=True, is_superuser=True
        )
        notification = EmailNotification(pk=123)

        self.assertFalse(admin_view.has_delete_permission(request))
        self.assertFalse(admin_view.has_delete_permission(request, notification))
        self.assertNotIn("delete_selected", admin_view.get_actions(request))


class AdminMiddlewareTests(SimpleTestCase):
    def test_session_user_middleware_keeps_admin_user(self):
        factory = RequestFactory()
        request = factory.get("/admin/")
        request.session = {}
        request.user = object()
        original_user = request.user

        response = SessionUserMiddleware(lambda req: req)(request)

        self.assertIs(response.user, original_user)
