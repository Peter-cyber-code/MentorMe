from rest_framework import serializers

from .models import (
    Conversation,
    ConversationParticipant,
    Message,
    MessageAttachment,
)


class MessageAttachmentSerializer(
    serializers.ModelSerializer
):

    class Meta:
        model = MessageAttachment

        fields = [
            "id",
            "file",
            "file_name",
            "uploaded_at",
        ]


class MessageSerializer(
    serializers.ModelSerializer
):

    attachments = MessageAttachmentSerializer(
        many=True,
        read_only=True
    )

    sender_name = serializers.SerializerMethodField()

    class Meta:
        model = Message

        fields = [
            "id",
            "conversation",
            "sender",
            "sender_name",
            "content",
            "reply_to",
            "attachments",
            "is_edited",
            "is_deleted",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "conversation",
            "sender",
            "is_edited",
            "is_deleted",
            "created_at",
            "updated_at",
        ]

    def get_sender_name(
        self,
        obj
    ):
        if not obj.sender:
            return None

        return (
            obj.sender.get_full_name()
            or obj.sender.username
        )


class ConversationParticipantSerializer(
    serializers.ModelSerializer
):

    username = serializers.CharField(
        source="user.username",
        read_only=True
    )

    full_name = serializers.SerializerMethodField()

    def get_full_name(self, obj):
        return obj.user.get_full_name() or obj.user.username

    class Meta:
        model = ConversationParticipant

        fields = [
            "id",
            "user",
            "username",
            "full_name",
            "joined_at",
            "last_read_at",
            "is_admin",
        ]


class ConversationSerializer(
    serializers.ModelSerializer
):

    memberships = ConversationParticipantSerializer(
        many=True,
        read_only=True
    )

    last_message = serializers.SerializerMethodField()

    class Meta:
        model = Conversation

        fields = [
            "id",
            "conversation_type",
            "name",
            "created_by",
            "memberships",
            "last_message",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "created_by",
            "created_at",
            "updated_at",
        ]

    def get_last_message(
        self,
        obj
    ):

        message = obj.messages.order_by(
            "-created_at"
        ).first()

        if not message:
            return None

        return MessageSerializer(
            message
        ).data