from rest_framework import serializers

from .models import Notification


class NotificationSerializer(
    serializers.ModelSerializer
):

    sender_name = serializers.SerializerMethodField()

    class Meta:
        model = Notification

        fields = [
            "id",
            "sender",
            "sender_name",
            "notification_type",
            "title",
            "message",
            "resource_type",
            "resource_id",
            "is_read",
            "created_at",
        ]

        read_only_fields = fields


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