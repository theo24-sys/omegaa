from django.db import models
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone


class Notification(models.Model):
    # Choices as class attributes (more readable & reusable)
    TYPE_JOB_APPLICATION   = 'job_application'
    TYPE_APPLICATION_STATUS = 'application_status'
    TYPE_MESSAGE           = 'message'
    TYPE_REVIEW            = 'review'
    TYPE_SYSTEM            = 'system'

    NOTIFICATION_TYPES = (
        (TYPE_JOB_APPLICATION,   'Job Application'),
        (TYPE_APPLICATION_STATUS, 'Application Status'),
        (TYPE_MESSAGE,           'New Message'),
        (TYPE_REVIEW,            'New Review'),
        (TYPE_SYSTEM,            'System Notification'),
    )

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name="Recipient"
    )

    notification_type = models.CharField(
        max_length=30,
        choices=NOTIFICATION_TYPES,
        db_index=True,              # speeds up filtering by type
        verbose_name="Type"
    )

    title = models.CharField(
        max_length=255,
        verbose_name="Title"
    )

    message = models.TextField(
        verbose_name="Message"
    )

    is_read = models.BooleanField(
        default=False,
        verbose_name="Read?",
        db_index=True            # fast unread queries
    )

    created_at = models.DateTimeField(
        default=timezone.now,    # better than auto_now_add in most cases
        editable=False,
        db_index=True
    )

    # Generic relation (optional — links to Job, Application, Review, etc.)
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notifications'
    )
    object_id = models.PositiveIntegerField(
        null=True,
        blank=True
    )
    content_object = GenericForeignKey('content_type', 'object_id')

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'is_read']),     # common unread query
            models.Index(fields=['recipient', 'notification_type']),
        ]
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"

    def __str__(self):
        return f"{self.title} ({self.get_notification_type_display()}) → {self.recipient}"

    # Convenience methods (very useful in templates & views)
    def mark_as_read(self):
        if not self.is_read:
            self.is_read = True
            self.save(update_fields=['is_read'])

    @classmethod
    def unread_count_for_user(cls, user):
        return cls.objects.filter(recipient=user, is_read=False).count()

    @property
    def icon_class(self):
        """Return Tailwind/Bootstrap icon class based on type (for frontend)"""
        icons = {
            self.TYPE_JOB_APPLICATION:   'fas fa-briefcase',
            self.TYPE_APPLICATION_STATUS: 'fas fa-info-circle',
            self.TYPE_MESSAGE:           'fas fa-envelope',
            self.TYPE_REVIEW:            'fas fa-star',
            self.TYPE_SYSTEM:            'fas fa-bell',
        }
        return icons.get(self.notification_type, 'fas fa-bell')