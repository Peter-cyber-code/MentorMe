from .models import Notification


def create_notification(
    *,
    recipient,
    notification_type,
    title,
    message="",
    sender=None,
    resource_type="",
    resource_id=None,
):

    if sender and sender == recipient:
        return None

    return Notification.objects.create(
        recipient=recipient,
        sender=sender,
        notification_type=notification_type,
        title=title,
        message=message,
        resource_type=resource_type,
        resource_id=resource_id,
    )