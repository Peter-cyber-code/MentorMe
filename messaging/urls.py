from django.urls import path

from .views import (
    ConversationListView,
    PrivateConversationCreateView,
    MessageListView,
    MessageCreateView,
    MessageManageView,
    MessageDeleteView,
    MarkConversationReadView,
)


urlpatterns = [

    path(
        "conversations/",
        ConversationListView.as_view(),
        name="conversation-list"
    ),

    path(
        "conversations/private/",
        PrivateConversationCreateView.as_view(),
        name="private-conversation-create"
    ),

    path(
        "conversations/<int:conversation_id>/messages/",
        MessageListView.as_view(),
        name="message-list"
    ),

    path(
        "conversations/<int:conversation_id>/messages/send/",
        MessageCreateView.as_view(),
        name="message-create"
    ),

    path(
        "messages/<int:pk>/",
        MessageManageView.as_view(),
        name="message-manage"
    ),

    path(
        "messages/<int:pk>/delete/",
        MessageDeleteView.as_view(),
        name="message-delete"
    ),

    path(
        "conversations/<int:conversation_id>/read/",
        MarkConversationReadView.as_view(),
        name="conversation-read"
    ),
]