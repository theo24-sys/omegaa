"""
Purge document files 24 hours after admin verification.
Run daily via cron: python manage.py purge_verified_docs

Files are deleted from storage to save space; documents_verified stays True.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

from accounts.models import CustomUser


class Command(BaseCommand):
    help = 'Delete document files (ID, Agreement, Police Clearance) 24h after verification to save storage'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be purged without deleting',
        )

    def handle(self, *args, **options):
        cutoff = timezone.now() - timedelta(hours=24)
        users = list(CustomUser.objects.filter(
            documents_verified=True,
            documents_verified_at__lt=cutoff,
        ))
        users = [u for u in users if u.id_document or u.agreement_form or u.police_clearance]

        if not users:
            self.stdout.write(self.style.SUCCESS('No documents to purge.'))
            return

        if options['dry_run']:
            self.stdout.write(f'Would purge docs for {len(users)} user(s):')
            for u in users:
                self.stdout.write(f'  - {u.username} (verified at {u.documents_verified_at})')
            return

        purged = 0
        for user in users:
            deleted_any = False
            for field in ('id_document', 'agreement_form', 'police_clearance'):
                f = getattr(user, field)
                if f:
                    try:
                        f.delete(save=False)
                        deleted_any = True
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f'  Could not delete {field} for {user.username}: {e}'))
            if deleted_any:
                user.id_document = None
                user.agreement_form = None
                user.police_clearance = None
                user.save(update_fields=['id_document', 'agreement_form', 'police_clearance'])
                purged += 1
                self.stdout.write(f'  Purged docs for {user.username}')

        self.stdout.write(self.style.SUCCESS(f'Purged documents for {purged} user(s).'))
