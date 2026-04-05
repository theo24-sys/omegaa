from django.contrib.contenttypes.models import ContentType
from .models import Notification

def create_notification(recipient, notification_type, title, message, related_object=None):
    """
    Utility to create a notification safely.
    """
    notification = Notification(
        recipient=recipient,
        notification_type=notification_type,
        title=title,
        message=message,
    )
    
    if related_object:
        notification.content_type = ContentType.objects.get_for_model(related_object.__class__)
        notification.object_id = related_object.pk
    
    notification.save()
    return notification