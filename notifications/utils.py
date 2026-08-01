from django.contrib.contenttypes.models import ContentType
from notifications.models import Notification
from .sms_utils import send_sms as dispatch_sms

def create_notification(recipient, notification_type, title, message, related_object=None, send_sms=False):
    """
    Utility to create a notification safely and optionally send an SMS.
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

    # SMS Dispatch
    if send_sms and recipient.phone_number:
        # We use title: message for the SMS content
        sms_text = f"Charlady: {title}\n{message}"
        dispatch_sms(recipient.phone_number, sms_text)
    
    return notification