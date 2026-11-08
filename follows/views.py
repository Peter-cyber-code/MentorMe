from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404

from rest_framework.permissions import (
    IsAuthenticated,
)

from rest_framework.response import Response

from rest_framework.views import APIView

from rest_framework import generics

from .models import Follow

from .serializers import (
    FollowSerializer,
)

from .pagination import (
    FollowPagination,
)


User = get_user_model()

class ToggleFollowView(
    APIView
):

    permission_classes = [
        IsAuthenticated
    ]

    def post(
        self,
        request,
        user_id
    ):

        user_to_follow = get_object_or_404(
            User,
            pk=user_id
        )

        if user_to_follow == request.user:

            return Response(
                {
                    "detail":
                    "Vous ne pouvez pas vous suivre vous-même."
                },
                status=400
            )

        follow = Follow.objects.filter(
            follower=request.user,
            following=user_to_follow
        ).first()

        if follow:

            follow.delete()

            following = False

        else:

            Follow.objects.create(
                follower=request.user,
                following=user_to_follow
            )

            following = True

        followers_count = (
            Follow.objects.filter(
                following=user_to_follow
            ).count()
        )

        return Response(
            {
                "following": following,
                "followers_count": followers_count
            }
        )


class FollowersListView(
    generics.ListAPIView
):

    serializer_class = FollowSerializer

    permission_classes = [
        IsAuthenticated
    ]

    pagination_class = FollowPagination

    def get_queryset(self):

        user = get_object_or_404(
            User,
            pk=self.kwargs["user_id"]
        )

        return (
            Follow.objects
            .filter(
                following=user
            )
            .select_related(
                "follower",
                "following"
            )
        )


class FollowingListView(
    generics.ListAPIView
):

    serializer_class = FollowSerializer

    permission_classes = [
        IsAuthenticated
    ]

    pagination_class = FollowPagination

    def get_queryset(self):

        user = get_object_or_404(
            User,
            pk=self.kwargs["user_id"]
        )

        return (
            Follow.objects
            .filter(
                follower=user
            )
            .select_related(
                "follower",
                "following"
            )
        )

class FollowStatusView(
    APIView
):

    permission_classes = [
        IsAuthenticated
    ]

    def get(
        self,
        request,
        user_id
    ):

        user = get_object_or_404(
            User,
            pk=user_id
        )

        is_following = (
            Follow.objects.filter(
                follower=request.user,
                following=user
            ).exists()
        )

        followers_count = (
            Follow.objects.filter(
                following=user
            ).count()
        )

        following_count = (
            Follow.objects.filter(
                follower=user
            ).count()
        )

        return Response(
            {
                "is_following": is_following,
                "followers_count": followers_count,
                "following_count": following_count,
            }
        )


class MyNetworkView(
    APIView
):

    permission_classes = [
        IsAuthenticated
    ]

    def get(
        self,
        request
    ):

        followers_count = (
            Follow.objects.filter(
                following=request.user
            ).count()
        )

        following_count = (
            Follow.objects.filter(
                follower=request.user
            ).count()
        )

        return Response(
            {
                "followers_count":
                    followers_count,

                "following_count":
                    following_count,
            }
        )