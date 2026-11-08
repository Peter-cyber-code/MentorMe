"""
Source unique de vérité pour les rôles.

Le système de rôles officiel est Profile.roles (codes de profiles.Role).
Le champ legacy CustomUser.user_type n'est plus utilisé par la logique métier.
"""

# Rôles qu'un utilisateur peut s'attribuer lui-même.
SELF_ASSIGNABLE_ROLE_CODES = {"project_owner", "collaborator"}

# Rôles qui exigent une vérification (Profile.is_verified) ou une attribution
# par un administrateur.
PRIVILEGED_ROLE_CODES = {
    "mentor",
    "investor",
    "financial_expert",
    "marketing_expert",
    "legal_expert",
}

# Rôles autorisés à publier des disponibilités et recevoir des réservations.
PROVIDER_ROLE_CODES = {
    "mentor",
    "financial_expert",
    "marketing_expert",
    "legal_expert",
}


def user_role_codes(user):
    """Retourne l'ensemble des codes de rôle de l'utilisateur."""
    if not user or not getattr(user, "is_authenticated", False):
        return set()
    profile = getattr(user, "profile", None)
    if profile is None:
        return set()
    return set(profile.roles.values_list("code", flat=True))


def is_provider(user):
    """Vrai si l'utilisateur peut recevoir des réservations."""
    return bool(user_role_codes(user) & PROVIDER_ROLE_CODES)
