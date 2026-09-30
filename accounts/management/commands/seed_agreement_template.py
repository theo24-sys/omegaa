"""
Seed the default worker agreement template into PlatformDocument.

Usage: python manage.py seed_agreement_template
Idempotent: only seeds if no active worker agreement exists yet, so an
admin-uploaded replacement is never overwritten.
"""
import os

from django.conf import settings
from django.core.files.base import File
from django.core.management.base import BaseCommand

from accounts.models import PlatformDocument

SOURCE_PDF = os.path.join(settings.BASE_DIR, 'platform_docs', 'charlady_househelp_agreement.pdf')


class Command(BaseCommand):
    help = 'Seed the default househelp agreement template (skipped if one already exists)'

    def handle(self, *args, **options):
        existing = PlatformDocument.objects.filter(doc_type='worker_agreement').first()
        if existing and existing.is_active:
            self.stdout.write(self.style.WARNING(f"Worker agreement already exists: {existing.name} — skipping."))
            return

        if not os.path.exists(SOURCE_PDF):
            self.stdout.write(self.style.ERROR(f"Default agreement PDF not found at {SOURCE_PDF}"))
            return

        with open(SOURCE_PDF, 'rb') as f:
            if existing:
                existing.document_file.save('charlady_househelp_agreement.pdf', File(f), save=False)
                existing.is_active = True
                existing.save()
                self.stdout.write(self.style.SUCCESS(f"Reactivated existing worker agreement: {existing.name}"))
            else:
                doc = PlatformDocument.objects.create(
                    name='Househelp Work Agreement (Default)',
                    doc_type='worker_agreement',
                    description='Official Charlady househelp agreement. Downloaded copies carry a unique Agreement ID in the filename.',
                )
                doc.document_file.save('charlady_househelp_agreement.pdf', File(f), save=True)
                self.stdout.write(self.style.SUCCESS(f"Seeded default worker agreement: {doc.name}"))
