from django.contrib.auth import get_user_model

from rest_framework import serializers

from .models import Follow


User = get_user_model()


class FollowUserSerializer(
    serializers.ModelSerializer
):

    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User

        fields = [
            "id",
            "username",
            "full_name",
        ]

    def get_full_name(
        self,
        obj
    ):
        return (
            obj.get_full_name()
            or obj.username
        )


class FollowSerializer(
    serializers.ModelSerializer
):

    follower = FollowUserSerializer(
        read_only=True
    )

    following = FollowUserSerializer(
        read_only=True
    )

    class Meta:
        model = Follow

        fields = [
            "id",
            "follower",
            "following",
            "created_at",
        ]

        read_only_fields = [
            "id",
            "follower",
            "following",
            "created_at",
        ]