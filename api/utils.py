from .models import Notification

def create_notification(recipient, sender, notification_type):
    Notification.objects.create(
        recipient=recipient,
        sender=sender,
        notification_type=notification_type
    )