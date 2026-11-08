from django.conf import settings
from django.db import models


User = settings.AUTH_USER_MODEL


class Conversation(models.Model):

    CONVERSATION_TYPES = [
        ("private", "Privée"),
        ("group", "Groupe"),
    ]

    conversation_type = models.CharField(
        max_length=20,
        choices=CONVERSATION_TYPES,
        default="private"
    )

    name = models.CharField(
        max_length=150,
        blank=True
    )

    participants = models.ManyToManyField(
        User,
        through="ConversationParticipant",
        related_name="conversations"
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_conversations"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = [
            "-updated_at"
        ]

    def __str__(self):
        return (
            self.name
            or f"Conversation {self.pk}"
        )


class ConversationParticipant(models.Model):

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="memberships"
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="conversation_memberships"
    )

    joined_at = models.DateTimeField(
        auto_now_add=True
    )

    last_read_at = models.DateTimeField(
        null=True,
        blank=True
    )

    is_admin = models.BooleanField(
        default=False
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "conversation",
                    "user"
                ],
                name="unique_conversation_participant"
            )
        ]


class Message(models.Model):

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages"
    )

    sender = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="sent_messages"
    )

    content = models.TextField(
        blank=True
    )

    reply_to = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="replies"
    )

    is_edited = models.BooleanField(
        default=False
    )

    is_deleted = models.BooleanField(
        default=False
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = [
            "created_at"
        ]

    def __str__(self):
        return f"Message {self.pk}"


class MessageAttachment(models.Model):

    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name="attachments"
    )

    file = models.FileField(
        upload_to="messages/"
    )

    file_name = models.CharField(
        max_length=255,
        blank=True
    )

    uploaded_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.file_name or self.file.name