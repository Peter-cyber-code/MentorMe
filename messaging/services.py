from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from notifications.services import create_notification


def message_payload(message):
    """Format unique des messages poussés en temps réel."""
    return {
        "id": message.id,
        "content": message.content,
        "sender": message.sender_id,
        "created_at": message.created_at.isoformat(),
        "attachments": [
            {"id": a.id, "file": a.file.url, "file_name": a.file_name}
            for a in message.attachments.all()
        ],
    }


def notify_participants(message):
    """Crée une notification pour chaque autre participant."""
    for membership in message.conversation.memberships.select_related("user"):
        create_notification(
            recipient=membership.user,
            sender=message.sender,
            notification_type="message",
            title="Nouveau message",
            message=(message.content or "Pièce jointe")[:140],
            resource_type="conversation",
            resource_id=message.conversation_id,
        )


def broadcast_message(message):
    """Diffuse un message créé via REST aux clients WebSocket connectés."""
    layer = get_channel_layer()
    if layer is None:
        return
    async_to_sync(layer.group_send)(
        f"conversation_{message.conversation_id}",
        {"type": "chat_message", "message": message_payload(message)},
    )
