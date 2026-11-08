from rest_framework.permissions import BasePermission

from profiles.roles import is_provider


class IsMentorOrExpert(BasePermission):
    """Mentors et experts (rôles du profil) uniquement."""

    message = (
        "Seuls les mentors et experts vérifiés "
        "peuvent gérer des disponibilités."
    )

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and is_provider(request.user)
        )
