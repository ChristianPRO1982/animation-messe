from __future__ import annotations

from django.core.management.base import BaseCommand

from app_main.mock_accounts import DEV_MOCK_ACCOUNTS
from app_main.models import DirectoryUserRecord
from app_member.models import Member

ACCOUNT_ROLE_BY_USERNAME = {
    "testmock": {"is_admin": True},
    "testmock_moderateur": {"is_admin": False},
    "testmock_simpletuser": {"is_admin": False},
    "disabled.user": {"is_admin": False},
}


class Command(BaseCommand):
    help = (
        "Synchronise les comptes auth_mock de dev dans users.users et les rôles "
        "locaux Animation Messe associés."
    )

    def handle(self, *args, **options):
        created_users = 0
        updated_users = 0
        created_members = 0
        updated_members = 0

        for account in DEV_MOCK_ACCOUNTS:
            if account["username"] == "unknown.user":
                Member.objects.filter(mm_id=account["external_id"]).delete()
                deleted_count, _details = DirectoryUserRecord.objects.filter(
                    id=account["external_id"]
                ).delete()
                if deleted_count:
                    self.stdout.write(
                        f"users.users cleared: {account['username']} "
                        f"({account['external_id']})"
                    )
                continue

            defaults = {
                "username": account["username"],
                "email": account["email"],
                "first_name": account["first_name"],
                "last_name": account["last_name"],
                "enabled": account["username"] != "disabled.user",
            }
            record, created = DirectoryUserRecord.objects.update_or_create(
                id=account["external_id"],
                defaults=defaults,
            )
            if created:
                created_users += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"users.users created: {record.username} ({record.id})"
                    )
                )
            else:
                updated_users += 1
                self.stdout.write(
                    f"users.users updated: {record.username} ({record.id})"
                )

            member_state = ACCOUNT_ROLE_BY_USERNAME.get(
                account["username"], {"is_admin": False}
            )
            member, member_created = Member.objects.update_or_create(
                mm_id=record.id,
                defaults=member_state,
            )
            if member_created:
                created_members += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"am.m_member created: {record.username} "
                        f"(admin={member.is_admin})"
                    )
                )
            else:
                updated_members += 1
                self.stdout.write(
                    f"am.m_member updated: {record.username} "
                    f"(admin={member.is_admin})"
                )

        self.stdout.write(
            self.style.SUCCESS(
                "sync_auth_mock_accounts completed "
                f"(users created={created_users}, users updated={updated_users}, "
                f"members created={created_members}, "
                f"members updated={updated_members})."
            )
        )
