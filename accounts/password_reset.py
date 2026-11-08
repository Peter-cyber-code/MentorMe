"""Réinitialisation du mot de passe par code à 6 chiffres (valable 15 minutes)."""
import secrets
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password, make_password
from django.core.mail import send_mail
from django.utils import timezone
from rest_framework_simplejwt.token_blacklist.models import (
    BlacklistedToken,
    OutstandingToken,
)

from .models import PasswordResetCode

CODE_TTL = timedelta(minutes=15)
MAX_ATTEMPTS = 5


def issue_code(user):
    """Crée un nouveau code (les précédents deviennent inutilisables)."""
    PasswordResetCode.objects.filter(user=user, used=False).update(used=True)
    code = f"{secrets.randbelow(1_000_000):06d}"
    PasswordResetCode.objects.create(user=user, code_hash=make_password(code))
    return code


def send_code_email(user, code):
    name = user.first_name or "Bonjour"
    send_mail(
        subject="Votre code de réinitialisation MentorMe",
        message=(
            f"Bonjour {name},\n\n"
            f"Votre code de réinitialisation MentorMe est : {code}\n\n"
            "Il est valable 15 minutes. Si vous n'êtes pas à l'origine de cette demande, "
            "ignorez simplement ce message : votre mot de passe reste inchangé.\n\n"
            "L'équipe MentorMe"
        ),
        from_email=None,
        recipient_list=[user.email],
        fail_silently=False,
    )


def active_code_for(user):
    limit = timezone.now() - CODE_TTL
    return PasswordResetCode.objects.filter(
        user=user, used=False, created_at__gte=limit
    ).first()


def check_code(user, code):
    """Vrai si le code est valide. Compte les essais et bloque après 5 erreurs."""
    entry = active_code_for(user)
    if entry is None:
        return None

    if not check_password(str(code), entry.code_hash):
        entry.attempts += 1
        if entry.attempts >= MAX_ATTEMPTS:
            entry.used = True
        entry.save(update_fields=["attempts", "used"])
        return None

    return entry


def revoke_sessions(user):
    """Déconnecte tous les appareils : les refresh tokens existants sont révoqués."""
    for token in OutstandingToken.objects.filter(user=user):
        BlacklistedToken.objects.get_or_create(token=token)


def find_user(email):
    return get_user_model().objects.filter(
        email__iexact=(email or "").strip(), is_active=True
    ).first()
