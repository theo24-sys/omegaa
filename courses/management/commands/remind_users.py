from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Q
from accounts.models import CustomUser
from notifications.models import Notification
from courses.models import Course, CourseCompletion

class Command(BaseCommand):
    help = 'Sends daily reminders to househelps about mandatory courses and verification'

    def handle(self, *args, **options):
        now = timezone.now()
        yesterday = now - timezone.timedelta(days=1)
        
        # Target househelps who haven't completed mandatory courses or are not verified
        users = CustomUser.objects.filter(
            user_type='househelp',
            is_active=True
        ).filter(
            Q(last_reminder_sent__isnull=True) | Q(last_reminder_sent__lt=yesterday)
        )
        
        mandatory_courses = Course.objects.filter(is_mandatory=True)
        
        sent_count = 0
        for user in users:
            # Check for incomplete mandatory courses
            completed_mandatory_count = CourseCompletion.objects.filter(
                user=user, 
                course__in=mandatory_courses
            ).count()
            
            needs_reminder = False
            message = ""
            
            if completed_mandatory_count < mandatory_courses.count():
                needs_reminder = True
                message = "Daily Reminder: Don't forget to complete your mandatory Professional Standards course to stand out to employers!"
            elif not user.is_verified:
                needs_reminder = True
                message = "Daily Reminder: Complete your account verification to start applying for premium jobs!"
            
            if needs_reminder:
                Notification.objects.create(
                    recipient=user,
                    notification_type='system',
                    title='Daily Reminder',
                    message=message
                )
                user.last_reminder_sent = now
                user.save()
                sent_count += 1
                
        self.stdout.write(self.style.SUCCESS(f'Successfully sent {sent_count} daily reminders.'))
