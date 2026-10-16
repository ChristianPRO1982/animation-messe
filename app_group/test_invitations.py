import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from email import policy
from email.parser import BytesParser
from io import StringIO
from types import SimpleNamespace
from unittest.mock import patch

from django.core import mail
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.management import call_command
from django.db import close_old_connections, transaction
from django.test import Client, TestCase, TransactionTestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from app_email.models import EmailNotification, EmailSettings
from app_email.services import send_private_email_now
from app_group import invitations, services
from app_group.models import (
    AmMember,
    AmMemberRequest,
    AmMemberTitle,
    CommonGroup,
    CommonGroupUser,
    Group,
    GroupFunction,
    GroupMember,
)
from app_main.models import DirectoryUserRecord
from app_member.models import Member

MEMORY_MAILERS = {
    "default": {"BACKEND": "django.core.mail.backends.locmem.EmailBackend"}
}


@override_settings(
    AM_EMAIL_ENABLED=True,
    MAILERS=MEMORY_MAILERS,
    AM_PUBLIC_ORIGIN="http://localhost:8000",
)
class InvitationTests(TestCase):
    def setUp(self):
        CommonGroup.objects.create(group_id=784310, name="Invitation test group")
        self.group = Group.objects.create(gg_id=784310)
        user_id = uuid.uuid4()
        DirectoryUserRecord.objects.create(id=user_id, username=str(user_id))
        Member.objects.create(mm_id=user_id)
        CommonGroupUser.objects.create(
            group_id=self.group.pk,
            member_id=user_id,
            am_access=True,
            is_group_admin=True,
        )
        self.actor = GroupMember.objects.create(
            group=self.group, member_id=user_id, member_kind="account"
        )
        EmailSettings.objects.update_or_create(pk=1, defaults={"enabled": True})

    def invite(self, **kwargs):
        results = []
        with self.captureOnCommitCallbacks(execute=True):
            invitation = invitations.invite_am_member(
                self.group,
                self.actor,
                first_name="Alice",
                last_name="Martin",
                email="alice@example.test",
                on_result=results.append,
                **kwargs,
            )
        invitation.refresh_from_db()
        return invitation, results

    def secret(self, kind):
        body = mail.outbox[-1].body
        url = next(line for line in body.splitlines() if f"/{kind}/#" in line)
        return url.split("#", 1)[1]

    def test_invitation_never_persists_email_or_raw_secrets(self):
        invitation, results = self.invite()
        trace = EmailNotification.objects.get(
            business_key=invitations.invitation_key(invitation)
        )
        self.assertEqual(results[0].status, "sent")
        self.assertEqual(trace.recipient_email, "")
        self.assertNotIn(
            "email", [field.name for field in AmMemberRequest._meta.fields]
        )
        self.assertNotIn(
            "consent_email_fingerprint", [field.name for field in AmMember._meta.fields]
        )
        self.assertNotIn(
            "alice@example.test", str(invitation.__dict__) + str(trace.__dict__)
        )
        self.assertNotIn(
            self.secret("consent"), str(invitation.__dict__) + str(trace.__dict__)
        )
        self.assertNotIn(
            self.secret("withdraw"), str(invitation.__dict__) + str(trace.__dict__)
        )
        self.assertIsNone(invitation.purge_at)
        self.assertFalse(AmMember.objects.exists())

    def test_no_send_on_rollback(self):
        with self.captureOnCommitCallbacks(execute=True) as callbacks:
            try:
                with transaction.atomic():
                    invitations.invite_am_member(
                        self.group,
                        self.actor,
                        first_name="Alice",
                        last_name="Martin",
                        email="alice@example.test",
                        on_result=lambda result: None,
                    )
                    raise ValueError("rollback")
            except ValueError:
                pass
        self.assertEqual(callbacks, [])
        self.assertFalse(AmMemberRequest.objects.exists())
        self.assertEqual(len(mail.outbox), 0)

    def test_private_delivery_is_idempotent(self):
        invitation, _ = self.invite()
        trace = send_private_email_now(
            invitations.INVITATION_TYPE,
            "different@example.test",
            {},
            business_key=invitations.invitation_key(invitation),
        )
        self.assertEqual(trace.status, "sent")
        self.assertEqual(len(mail.outbox), 1)

    def test_private_smtp_uses_tls_and_transient_recipient(self):
        smtp_mailers = {
            "default": {
                "BACKEND": "django.core.mail.backends.smtp.EmailBackend",
                "OPTIONS": {
                    "host": "smtp.example.test",
                    "port": 587,
                    "use_tls": True,
                    "use_ssl": False,
                    "username": "test-user",
                    "password": "fake-test-password",
                    "timeout": 10,
                },
            }
        }
        with (
            override_settings(MAILERS=smtp_mailers),
            patch("django.core.mail.backends.smtp.smtplib.SMTP") as smtp,
        ):
            smtp.return_value.sendmail.return_value = {}
            _, results = self.invite()
        self.assertEqual(results[0].status, "sent")
        self.assertEqual(results[0].recipient_email, "")
        smtp.return_value.starttls.assert_called_once()
        smtp.return_value.login.assert_called_once_with(
            "test-user", "fake-test-password"
        )
        _, recipients, message = smtp.return_value.sendmail.call_args.args
        self.assertEqual(recipients, ["alice@example.test"])
        parsed = BytesParser(policy=policy.default).parsebytes(message)
        self.assertEqual(
            [part.get_content_type() for part in parsed.iter_parts()],
            ["text/plain", "text/html"],
        )

    def test_blocked_request_is_due_after_seven_days(self):
        for server, admin, status in (
            (False, False, "blocked_env"),
            (False, True, "blocked_env"),
            (True, False, "blocked_admin"),
        ):
            with (
                self.subTest(server=server, admin=admin),
                override_settings(AM_EMAIL_ENABLED=server),
            ):
                EmailSettings.objects.filter(pk=1).update(enabled=admin)
                invitation, result = self.invite()
                self.assertEqual(result[0].status, status)
                self.assertEqual(
                    invitation.purge_at, invitation.created_at + timedelta(days=7)
                )
                self.assertEqual(len(mail.outbox), 0)

    def test_backend_failure_has_safe_trace_and_seven_day_purge(self):
        with (
            patch(
                "django.core.mail.EmailMultiAlternatives.send",
                side_effect=RuntimeError("token=secret alice@example.test"),
            ),
            self.assertLogs("app_email", level="ERROR") as logs,
        ):
            invitation, results = self.invite()
        self.assertEqual(results[0].status, "failed")
        self.assertIsNotNone(invitation.purge_at)
        self.assertNotIn(
            "alice@example.test", str(logs.output) + results[0].error_message
        )
        self.assertNotIn("token=secret", str(logs.output) + results[0].error_message)

    def test_acceptance_and_withdrawal_use_original_email_links(self):
        invitation, _ = self.invite()
        validation, removal = self.secret("consent"), self.secret("withdraw")
        profile = invitations.consent_decision(
            invitation.public_id, validation, action="accept"
        )
        self.assertEqual((profile.first_name, profile.last_name), ("Alice", "Martin"))
        self.assertEqual(profile.public_id, invitation.public_id)
        self.assertFalse(AmMemberRequest.objects.filter(pk=invitation.pk).exists())
        self.assertTrue(
            services.check_personal_secret(removal, profile.withdrawal_secret_hash)
        )
        with self.assertRaises(ValidationError):
            invitations.consent_decision(
                invitation.public_id, validation, action="accept"
            )
        invitations.withdraw(invitation.public_id, removal)
        self.assertTrue(AmMember.objects.filter(pk=profile.pk).exists())
        invitations.withdraw(invitation.public_id, removal, confirm=True)
        self.assertFalse(AmMember.objects.exists())
        self.assertFalse(
            GroupMember.objects.filter(pk=profile.group_member_id).exists()
        )

    def test_refusal_and_cancellation_do_not_create_member(self):
        invitation, _ = self.invite()
        invitations.consent_decision(
            invitation.public_id, self.secret("consent"), action="refuse"
        )
        self.assertFalse(AmMemberRequest.objects.filter(pk=invitation.pk).exists())
        invitation, _ = self.invite()
        invitations.withdraw(
            invitation.public_id, self.secret("withdraw"), confirm=True
        )
        self.assertFalse(AmMemberRequest.objects.filter(pk=invitation.pk).exists())
        self.assertFalse(AmMember.objects.exists())

    def test_invalid_expired_and_cross_purpose_tokens_are_rejected(self):
        invitation, _ = self.invite()
        for token in ("invalid", self.secret("withdraw")):
            with self.assertRaises(ValidationError):
                invitations.consent_decision(
                    invitation.public_id, token, action="accept"
                )
        AmMemberRequest.objects.filter(pk=invitation.pk).update(
            expires_at=timezone.now()
        )
        with self.assertRaises(ValidationError):
            invitations.consent_decision(
                invitation.public_id, self.secret("consent"), action="accept"
            )

    def test_fallback_consent_is_frozen(self):
        invitation, _ = self.invite()
        original = invitation.consent_body_markdown
        with patch(
            "app_group.services.default_consent_markdown", return_value="Nouveau texte"
        ):
            profile = invitations.consent_decision(
                invitation.public_id, self.secret("consent"), action="accept"
            )
        self.assertEqual(profile.consent_body_markdown, original)

    def test_identity_is_immutable_and_title_functions_are_editable(self):
        invitation, _ = self.invite()
        profile = invitations.consent_decision(
            invitation.public_id, self.secret("consent"), action="accept"
        )
        profile.first_name = "Autre"
        with self.assertRaises(ValidationError):
            profile.save()
        title = AmMemberTitle.objects.create(group=self.group, label="Choriste")
        function = GroupFunction.objects.create(group=self.group, name="Chant")
        user = SimpleNamespace(
            is_authenticated=True, is_admin=False, external_id=self.actor.member_id
        )
        membership = CommonGroupUser.objects.get(
            group_id=self.group.pk, member_id=self.actor.member_id
        )
        membership.is_group_admin = False
        membership.save(update_fields=["is_group_admin"])
        invitations.update_am_member(
            user,
            self.group,
            profile.group_member_id,
            title_id=title.pk,
            function_ids=[function.pk],
        )
        with self.assertRaises(PermissionDenied):
            invitations.delete_am_member(user, self.group, profile.group_member_id)
        membership.am_access = False
        membership.save(update_fields=["am_access"])
        with self.assertRaises(PermissionDenied):
            invitations.update_am_member(user, self.group, profile.group_member_id)
        profile.refresh_from_db()
        self.assertEqual(profile.title_id, title.pk)
        self.assertEqual(profile.group_member.function_assignments.count(), 1)
        invitations.delete_am_member(
            SimpleNamespace(is_authenticated=True, is_admin=True),
            self.group,
            profile.group_member_id,
        )
        self.assertFalse(AmMember.objects.exists())
        self.assertFalse(profile.group_member.function_assignments.exists())

    def test_cross_group_mutations_and_unknown_ids_are_rejected(self):
        invitation, _ = self.invite()
        profile = invitations.consent_decision(
            invitation.public_id, self.secret("consent"), action="accept"
        )
        CommonGroup.objects.create(group_id=784312, name="Other invitation test group")
        other = Group.objects.create(gg_id=784312)
        admin = SimpleNamespace(is_authenticated=True, is_admin=True)
        with self.assertRaises(ValidationError):
            invitations.update_am_member(admin, other, profile.group_member_id)
        with self.assertRaises(ValidationError):
            invitations.delete_am_member(admin, other, profile.group_member_id)
        self.assertTrue(AmMember.objects.filter(pk=profile.pk).exists())

    def test_console_cannot_print_private_messages(self):
        with (
            override_settings(
                MAILERS={
                    "default": {
                        "BACKEND": "django.core.mail.backends.console.EmailBackend"
                    }
                }
            ),
            self.assertLogs("app_email", level="ERROR"),
        ):
            invitation, results = self.invite()
        self.assertEqual(results[0].status, "failed")
        self.assertEqual(results[0].recipient_email, "")
        self.assertIsNotNone(invitation.purge_at)

    def test_untrusted_public_origins_are_rejected_before_creation(self):
        for origin in (
            "http://example.test",
            "https://user:secret@example.test",
            "https://example.test/path",
            "https://example.test?query=1",
            "",
        ):
            with (
                self.subTest(origin=origin),
                override_settings(AM_PUBLIC_ORIGIN=origin),
                self.assertRaises(ValidationError),
            ):
                self.invite()
        self.assertFalse(AmMemberRequest.objects.exists())

    def test_ordinary_members_can_update_but_not_invite_delete_or_edit_identity(self):
        invitation, _ = self.invite()
        profile = invitations.consent_decision(
            invitation.public_id, self.secret("consent"), action="accept"
        )
        membership = CommonGroupUser.objects.get(
            group_id=self.group.pk, member_id=self.actor.member_id
        )
        membership.is_group_admin = False
        membership.save(update_fields=["is_group_admin"])
        user = SimpleNamespace(
            is_authenticated=True,
            is_admin=False,
            external_id=str(self.actor.member_id),
            username="tester",
        )
        client = Client()
        url = reverse("group_am_members", args=[self.group.pk])
        with patch("app_main.middleware.refresh_request_user", return_value=user):
            page = client.get(url)
            self.assertEqual(page.status_code, 200)
            self.assertNotContains(page, "Créer l’invitation")
            self.assertContains(page, "Enregistrer")
            self.assertEqual(
                client.post(
                    url,
                    {
                        "action": "update_am_member",
                        "group_member_id": profile.group_member_id,
                    },
                ).status_code,
                302,
            )
            self.assertEqual(
                client.post(
                    url,
                    {
                        "action": "delete_am_member",
                        "group_member_id": profile.group_member_id,
                        "confirmed": "on",
                    },
                ).status_code,
                403,
            )
            self.assertEqual(
                client.post(
                    url,
                    {
                        "action": "create_am_member_request",
                        "first_name": "Bob",
                        "last_name": "Martin",
                        "email": "bob@example.test",
                    },
                ).status_code,
                403,
            )
            client.post(
                url,
                {
                    "action": "update_am_member",
                    "group_member_id": profile.group_member_id,
                    "first_name": "Changed",
                },
            )
        profile.refresh_from_db()
        self.assertEqual(profile.first_name, "Alice")

    def test_manual_purge_respects_exact_deadlines_and_dry_run(self):
        with override_settings(AM_EMAIL_ENABLED=False):
            invitation, _ = self.invite()
        deadline = invitation.purge_at
        output = StringIO()
        with patch(
            "app_group.management.commands.purge_am_member_requests.timezone.now",
            return_value=deadline - timedelta(microseconds=1),
        ):
            call_command("purge_am_member_requests", stdout=output)
        self.assertTrue(AmMemberRequest.objects.filter(pk=invitation.pk).exists())
        with patch(
            "app_group.management.commands.purge_am_member_requests.timezone.now",
            return_value=deadline,
        ):
            call_command("purge_am_member_requests", dry_run=True, stdout=output)
            self.assertTrue(AmMemberRequest.objects.filter(pk=invitation.pk).exists())
            call_command("purge_am_member_requests", stdout=output)
        self.assertFalse(AmMemberRequest.objects.filter(pk=invitation.pk).exists())

    def test_public_page_requires_secret_and_csrf_and_explicit_confirmation(self):
        invitation, _ = self.invite()
        client = Client(enforce_csrf_checks=True)
        url = reverse("am_member_consent", args=[invitation.public_id])
        response = client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Alice")
        self.assertIn("no-store", response["Cache-Control"])
        self.assertEqual(response["Referrer-Policy"], "no-referrer")
        self.assertIn("connect-src 'self'", response["Content-Security-Policy"])
        self.assertEqual(
            client.post(
                url,
                {
                    "secret": self.secret("consent"),
                    "action": "accept",
                    "confirmed": "on",
                },
            ).status_code,
            403,
        )
        csrf = client.cookies["csrftoken"].value
        data = {"secret": self.secret("consent"), "csrfmiddlewaretoken": csrf}
        preview = client.post(url, {**data, "action": "preview"})
        self.assertContains(preview, "Alice")
        self.assertInHTML(
            '<button name="action" value="accept" type="submit" data-requires-confirmation disabled>Accepter</button>',
            preview.content.decode(),
        )
        self.assertFalse(AmMember.objects.exists())
        self.assertEqual(
            client.post(url, {**data, "action": "accept"}).status_code, 400
        )
        self.assertEqual(
            client.post(
                url, {**data, "action": "accept", "confirmed": "on"}
            ).status_code,
            200,
        )
        removal = reverse("am_member_withdraw", args=[invitation.public_id])
        self.assertEqual(client.get(removal).status_code, 200)
        self.assertTrue(AmMember.objects.exists())
        self.assertEqual(
            client.post(
                removal, {**data, "secret": self.secret("withdraw"), "action": "delete"}
            ).status_code,
            400,
        )
        self.assertTrue(AmMember.objects.exists())


class ConcurrentConsentTests(TransactionTestCase):
    def test_concurrent_acceptances_create_one_profile(self):
        common_group = CommonGroup.objects.create(
            group_id=784311, name="Concurrent invitation test group"
        )
        self.addCleanup(lambda: CommonGroup.objects.filter(pk=common_group.pk).delete())
        group = Group.objects.create(gg_id=784311)
        invitation = AmMemberRequest.objects.create(
            group=group,
            first_name="Alice",
            last_name="Martin",
            consent_token_hash=services.hash_personal_secret("validation"),
            withdrawal_secret_hash=services.hash_personal_secret("withdrawal"),
            consent_version="v1",
            consent_body_markdown="Texte",
            expires_at=timezone.now() + timedelta(days=14),
        )
        self.addCleanup(lambda: Group.objects.filter(pk=group.pk).delete())

        def accept():
            close_old_connections()
            try:
                invitations.consent_decision(
                    invitation.public_id, "validation", action="accept"
                )
                return True
            except ValidationError:
                return False
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: accept(), range(2)))
        self.assertEqual(sorted(results), [False, True])
        self.assertEqual(
            AmMember.objects.filter(public_id=invitation.public_id).count(), 1
        )
