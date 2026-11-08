from rest_framework.permissions import (
    BasePermission,
)


class IsConversationParticipant(
    BasePermission
):

    def has_object_permission(
        self,
        request,
        view,
        obj
    ):

        conversation = getattr(
            obj,
            "conversation",
            obj
        )

        return conversation.memberships.filter(
            user=request.user
        ).exists()


class IsMessageSender(
    BasePermission
):

    def has_object_permission(
        self,
        request,
        view,
        obj
    ):

        return obj.sender == request.user