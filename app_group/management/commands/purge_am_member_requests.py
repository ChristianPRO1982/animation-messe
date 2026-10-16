from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone

from app_group.models import AmMemberRequest


class Command(BaseCommand):
    help = "Supprime les demandes Membre AM arrivées à échéance, sans envoyer d'email."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        now = timezone.now()
        requests = AmMemberRequest.objects.filter(
            Q(purge_at__lte=now) | Q(expires_at__lte=now)
        )
        count = requests.count()
        if not options["dry_run"]:
            requests.delete()
        self.stdout.write(
            f"Demandes {'à supprimer' if options['dry_run'] else 'supprimées'} : {count}"
        )
