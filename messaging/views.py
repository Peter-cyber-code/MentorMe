from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.utils import timezone

from config.uploads import validate_attachments
from rest_framework.exceptions import ValidationError
from rest_framework import generics
from rest_framework.exceptions import PermissionDenied
from rest_framework.parsers import (
    MultiPartParser,
    FormParser,
    JSONParser,
)
from rest_framework.permissions import (
    IsAuthenticated,
)
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    Conversation,
    ConversationParticipant,
    Message,
    MessageAttachment,
)

from .serializers import (
    ConversationSerializer,
    MessageSerializer,
)

from .pagination import (
    MessagePagination,
)
from .services import (
    broadcast_message,
    notify_participants,
)

from .permissions import (
    IsConversationParticipant,
    IsMessageSender,
)


User = get_user_model()


# Conversation de l'utilisateur

class ConversationListView(
    generics.ListAPIView
):

    serializer_class = ConversationSerializer

    permission_classes = [
        IsAuthenticated
    ]

    def get_queryset(self):

        return (
            Conversation.objects
            .filter(
                memberships__user=self.request.user
            )
            .distinct()
            .order_by("-updated_at")
        )

# création d'une conversation privée 

class PrivateConversationCreateView(
    APIView
):

    permission_classes = [
        IsAuthenticated
    ]

    def post(
        self,
        request
    ):

        user_id = request.data.get(
            "user_id"
        )

        other_user = get_object_or_404(
            User,
            pk=user_id
        )

        if other_user == request.user:

            return Response(
                {
                    "detail":
                    "Impossible de créer une conversation avec vous-même."
                },
                status=400
            )

        existing = (
            Conversation.objects
            .filter(
                conversation_type="private",
                memberships__user=request.user
            )
            .filter(
                memberships__user=other_user
            )
            .distinct()
            .first()
        )

        if existing:

            return Response(
                ConversationSerializer(
                    existing
                ).data
            )

        conversation = Conversation.objects.create(
            conversation_type="private",
            created_by=request.user
        )

        ConversationParticipant.objects.create(
            conversation=conversation,
            user=request.user
        )

        ConversationParticipant.objects.create(
            conversation=conversation,
            user=other_user
        )

        return Response(
            ConversationSerializer(
                conversation
            ).data,
            status=201
        )


# Historique des messages 

class MessageListView(
    generics.ListAPIView
):

    serializer_class = MessageSerializer

    permission_classes = [
        IsAuthenticated
    ]

    pagination_class = MessagePagination

    def get_queryset(self):

        conversation = get_object_or_404(
            Conversation,
            pk=self.kwargs["conversation_id"]
        )

        if not conversation.memberships.filter(
            user=self.request.user
        ).exists():

            raise PermissionDenied(
                "Vous n'avez pas accès à cette conversation."
            )

        return (
            Message.objects
            .filter(
                conversation=conversation
            )
            .select_related(
                "sender",
                "reply_to"
            )
            .prefetch_related(
                "attachments"
            )
            .order_by("-created_at")
        )


#Envoie d'un message

class MessageCreateView(
    generics.CreateAPIView
):

    serializer_class = MessageSerializer

    permission_classes = [
        IsAuthenticated
    ]

    parser_classes = [
        MultiPartParser,
        FormParser,
        JSONParser,
    ]

    def perform_create(
        self,
        serializer
    ):

        conversation = get_object_or_404(
            Conversation,
            pk=self.kwargs["conversation_id"]
        )

        if not conversation.memberships.filter(
            user=self.request.user
        ).exists():

            raise PermissionDenied(
                "Vous n'avez pas accès à cette conversation."
            )

        uploads = self.request.FILES.getlist(
            "attachments"
        )

        validate_attachments(uploads)

        text = (
            serializer.validated_data.get("content") or ""
        ).strip()

        if not text and not uploads:
            raise ValidationError(
                {"content": "Le message est vide."}
            )

        message = serializer.save(
            sender=self.request.user,
            conversation=conversation
        )

        files = self.request.FILES.getlist(
            "attachments"
        )

        for file in files:

            MessageAttachment.objects.create(
                message=message,
                file=file,
                file_name=file.name
            )

        notify_participants(message)
        broadcast_message(message)

# Modifier ou supprimer un message 

class MessageManageView(
    generics.RetrieveUpdateAPIView
):

    queryset = Message.objects.all()

    serializer_class = MessageSerializer

    permission_classes = [
        IsAuthenticated,
        IsMessageSender
    ]

    def perform_update(
        self,
        serializer
    ):

        serializer.save(
            is_edited=True
        )

class MessageDeleteView(
    APIView
):

    permission_classes = [
        IsAuthenticated
    ]

    def delete(
        self,
        request,
        pk
    ):

        message = get_object_or_404(
            Message,
            pk=pk
        )

        if message.sender != request.user:

            raise PermissionDenied(
                "Vous ne pouvez pas supprimer ce message."
            )

        message.content = ""

        message.is_deleted = True

        message.save(
            update_fields=[
                "content",
                "is_deleted",
                "updated_at",
            ]
        )

        return Response(
            {
                "detail":
                "Message supprimé."
            }
        )


# Messages lus 

class MarkConversationReadView(
    APIView
):

    permission_classes = [
        IsAuthenticated
    ]

    def post(
        self,
        request,
        conversation_id
    ):

        participant = get_object_or_404(
            ConversationParticipant,
            conversation_id=conversation_id,
            user=request.user
        )

        participant.last_read_at = (
            timezone.now()
        )

        participant.save(
            update_fields=[
                "last_read_at"
            ]
        )

        return Response(
            {
                "detail":
                "Conversation marquée comme lue."
            }
        )