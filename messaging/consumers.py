import json

from channels.db import (
    database_sync_to_async,
)

from channels.generic.websocket import (
    AsyncWebsocketConsumer,
)

from .models import (
    Conversation,
    Message,
)
from .services import (
    message_payload,
    notify_participants,
)


class ChatConsumer(
    AsyncWebsocketConsumer
):

    async def connect(self):

        self.user = self.scope["user"]

        if (
            not self.user
            or not self.user.is_authenticated
        ):
            await self.close()
            return

        self.conversation_id = (
            self.scope["url_route"]
            ["kwargs"]
            ["conversation_id"]
        )

        allowed = (
            await self.user_can_access()
        )

        if not allowed:
            await self.close()
            return

        self.room_group_name = (
            f"conversation_{self.conversation_id}"
        )

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()


    async def disconnect(
        self,
        close_code
    ):

        if hasattr(
            self,
            "room_group_name"
        ):

            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )


    async def receive(
        self,
        text_data
    ):

        try:
            data = json.loads(text_data)
        except (TypeError, ValueError):
            return

        if not isinstance(data, dict):
            return

        content = str(data.get("content", "")).strip()

        if not content or len(content) > 5000:
            return

        message = await self.save_message(
            content
        )

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "message": {
                    "id": message["id"],
                    "content": message["content"],
                    "sender": message["sender"],
                    "created_at":
                        message["created_at"],
                }
            }
        )


    async def chat_message(
        self,
        event
    ):

        await self.send(
            text_data=json.dumps(
                event["message"]
            )
        )


    @database_sync_to_async
    def user_can_access(self):

        return (
            Conversation.objects
            .filter(
                pk=self.conversation_id,
                memberships__user=self.user
            )
            .exists()
        )


    @database_sync_to_async
    def save_message(
        self,
        content
    ):

        conversation = (
            Conversation.objects.get(
                pk=self.conversation_id
            )
        )

        message = Message.objects.create(
            conversation=conversation,
            sender=self.user,
            content=content
        )

        notify_participants(message)

        return message_payload(message)
