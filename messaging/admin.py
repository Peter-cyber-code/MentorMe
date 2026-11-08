from django.contrib import admin

from .models import (
    Conversation,
    ConversationParticipant,
    Message,
    MessageAttachment,
)


class ParticipantInline(
    admin.TabularInline
):

    model = ConversationParticipant

    extra = 0


@admin.register(Conversation)
class ConversationAdmin(
    admin.ModelAdmin
):

    list_display = [
        "id",
        "conversation_type",
        "name",
        "created_by",
        "created_at",
        "updated_at",
    ]

    list_filter = [
        "conversation_type",
    ]

    inlines = [
        ParticipantInline
    ]


@admin.register(Message)
class MessageAdmin(
    admin.ModelAdmin
):

    list_display = [
        "id",
        "conversation",
        "sender",
        "is_edited",
        "is_deleted",
        "created_at",
    ]

    search_fields = [
        "content",
    ]


admin.site.register(
    MessageAttachment
)