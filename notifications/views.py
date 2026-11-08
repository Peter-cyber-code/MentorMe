from django.shortcuts import get_object_or_404

from rest_framework import generics
from rest_framework.permissions import (
    IsAuthenticated,
)
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Notification
from .serializers import NotificationSerializer
from .pagination import NotificationPagination


class NotificationListView(
    generics.ListAPIView
):

    serializer_class = NotificationSerializer

    permission_classes = [
        IsAuthenticated
    ]

    pagination_class = NotificationPagination

    def get_queryset(self):

        return Notification.objects.filter(
            recipient=self.request.user
        ).select_related(
            "sender"
        )


class MarkNotificationReadView(
    APIView
):

    permission_classes = [
        IsAuthenticated
    ]

    def post(
        self,
        request,
        pk
    ):

        notification = get_object_or_404(
            Notification,
            pk=pk,
            recipient=request.user
        )

        notification.is_read = True

        notification.save(
            update_fields=[
                "is_read"
            ]
        )

        return Response(
            {
                "is_read": True
            }
        )

class MarkAllNotificationsReadView(
    APIView
):

    permission_classes = [
        IsAuthenticated
    ]

    def post(
        self,
        request
    ):

        updated = (
            Notification.objects
            .filter(
                recipient=request.user,
                is_read=False
            )
            .update(
                is_read=True
            )
        )

        return Response(
            {
                "updated": updated
            }
        )

class UnreadNotificationCountView(
    APIView
):

    permission_classes = [
        IsAuthenticated
    ]

    def get(
        self,
        request
    ):

        count = (
            Notification.objects
            .filter(
                recipient=request.user,
                is_read=False
            )
            .count()
        )

        return Response(
            {
                "unread_count": count
            }
        )

