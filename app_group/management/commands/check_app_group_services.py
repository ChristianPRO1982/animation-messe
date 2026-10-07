from __future__ import annotations

import secrets
import uuid
from datetime import time
from types import SimpleNamespace

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import OperationalError, connection, transaction
from django.utils import timezone

from app_group import services
from app_group.models import (
    MEMBER_KIND_AM,
    CommonGroup,
    CommonGroupTag,
    CommonGroupUser,
    GroupFunction,
    GroupLocation,
    GroupMemberFunction,
    GroupMemberRole,
    SongTagVerse,
)
from app_main.models import DirectoryUserRecord
from app_member.models import Member


class Command(BaseCommand):
    help = (
        "Run PostgreSQL-backed app_group service checks inside a rolled-back "
        "transaction."
    )

    def handle(self, *args, **options):
        if connection.vendor != "postgresql":
            raise CommandError("check_app_group_services requiert PostgreSQL.")

        try:
            connection.ensure_connection()
        except OperationalError as exc:
            raise CommandError(
                "Connexion PostgreSQL indisponible pour check_app_group_services."
            ) from exc

        warnings = []
        with transaction.atomic():
            self._run_checks(warnings)
            transaction.set_rollback(True)

        for warning in warnings:
            self.stdout.write(self.style.WARNING(warning))
        self.stdout.write(self.style.SUCCESS("app_group service checks passed."))

    def _run_checks(self, warnings: list[str]) -> None:
        group_id = _transient_group_id()
        member_id = uuid.uuid4()
        token = "transient-consent-token"
        withdrawal_secret = "transient-withdrawal-secret"

        CommonGroup.objects.create(
            group_id=group_id,
            name=f"app_group check {group_id}",
            info="Transient service check row.",
            status=CommonGroup.STATUS_PRIVATE,
        )
        DirectoryUserRecord.objects.create(
            id=member_id,
            username=f"app-group-check-{member_id}",
            first_name="Check",
            last_name="AppGroup",
            email=f"app-group-check-{member_id}@example.invalid",
            enabled=True,
            email_verified=True,
        )
        Member.objects.create(mm_id=member_id, is_admin=False)
        CommonGroupUser.objects.create(
            group_id=group_id,
            member_id=member_id,
            is_group_admin=True,
            am_access=True,
        )

        group = services.ensure_group_environment(group_id)
        user = SimpleNamespace(
            is_authenticated=True,
            is_admin=False,
            external_id=str(member_id),
        )
        if not services.can_manage_group(user, group):
            raise CommandError("Le Responsable commun ne peut pas gérer le groupe.")

        _assert_raises_validation_error(
            lambda: services.set_common_responsable(
                group_id,
                str(member_id),
                enabled=False,
            ),
            "Le dernier Responsable commun n'est pas protégé.",
        )

        account_member = group.members.create(
            member_id=member_id,
            member_kind="account",
            joined_at=timezone.now(),
        )
        function = GroupFunction.objects.create(group=group, name="Animateur")
        request = services.create_am_member_request(
            group,
            account_member,
            first_name="Aline",
            last_name="Martin",
            email="aline.martin@example.invalid",
            consent_token=token,
            consent_version="check-v1",
        )
        if request.consent_token_hash == token:
            raise CommandError("Le jeton de consentement est stocké en clair.")

        am_member = services.accept_am_member_request(
            request,
            consent_token=token,
            withdrawal_secret=withdrawal_secret,
            functions=[function],
        )
        if am_member.group_member.member_kind != MEMBER_KIND_AM:
            raise CommandError("L'acceptation ne crée pas un Membre AM.")
        if am_member.withdrawal_secret_hash == withdrawal_secret:
            raise CommandError("Le secret de retrait est stocké en clair.")
        if not services.check_personal_secret(
            withdrawal_secret,
            am_member.withdrawal_secret_hash,
        ):
            raise CommandError("Le secret de retrait haché ne se vérifie pas.")
        if not GroupMemberFunction.objects.filter(
            group_member=am_member.group_member,
            function=function,
        ).exists():
            raise CommandError("La fonction du Membre AM n'a pas été associée.")

        _assert_raises_validation_error(
            lambda: services.assign_responsable_impression(am_member.group_member),
            "Un Membre AM peut recevoir un rôle applicatif.",
        )
        if GroupMemberRole.objects.filter(
            group_member=am_member.group_member,
        ).exists():
            raise CommandError("Un rôle applicatif a été persisté pour un Membre AM.")

        location = GroupLocation.objects.create(group=group, name="Eglise test")
        services.create_celebration_rule(
            group,
            weekday=6,
            time=time(10, 30),
            location=location,
        )

        self._check_repertoire_services(group, group_id, warnings)

    def _check_repertoire_services(self, group, group_id: int, warnings: list[str]):
        lss_song_id, verse_ids = _first_lss_references()
        if lss_song_id is None or not verse_ids:
            warnings.append(
                "Controle recueil ignore : aucune donnee lss.s_songs/lss.s_verses."
            )
            return

        group_tag = CommonGroupTag.objects.create(
            gt_id=_transient_bigint_id(),
            group_id=group_id,
            name="Tag controle app_group",
            sort_order=0,
            is_active=True,
        )
        song = services.add_song_to_repertoire(
            group,
            song_id=lss_song_id,
            verse_ids=verse_ids,
        )
        song_tag = services.tag_song(song, group_tag)
        selection_count = SongTagVerse.objects.filter(song_tag=song_tag).count()
        if selection_count != len(set(verse_ids)):
            raise CommandError("Les SongTagVerse n'ont pas ete initialises.")


def _transient_group_id() -> int:
    return 900_000_000 + secrets.randbelow(90_000_000)


def _transient_bigint_id() -> int:
    return 9_000_000_000_000 + secrets.randbelow(900_000_000_000)


def _first_lss_references() -> tuple[int | None, list[int]]:
    with connection.cursor() as cursor:
        cursor.execute(
            'SELECT "song_id" FROM "lss"."s_songs" ORDER BY "song_id" LIMIT 1'
        )
        song_row = cursor.fetchone()
        cursor.execute(
            'SELECT "verse_id" FROM "lss"."s_verses" ORDER BY "verse_id" LIMIT 3'
        )
        verse_rows = cursor.fetchall()
    song_id = song_row[0] if song_row else None
    verse_ids = [row[0] for row in verse_rows]
    return song_id, verse_ids


def _assert_raises_validation_error(callback, message: str) -> None:
    try:
        callback()
    except ValidationError:
        return
    raise CommandError(message)
