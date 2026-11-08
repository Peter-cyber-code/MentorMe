"""Initialisation d'un serveur neuf (lancée à chaque démarrage, sans danger).

Variables d'environnement :
  ADMIN_EMAIL, ADMIN_PASSWORD   crée (ou met à jour) le compte administrateur
  SEED_DEMO=1                    charge les données de démonstration
"""
import os

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Crée l'administrateur et (option) les données de démonstration."

    def handle(self, *args, **options):
        User = get_user_model()
        email = (os.environ.get("ADMIN_EMAIL") or "").strip()
        password = os.environ.get("ADMIN_PASSWORD") or ""

        if email and password:
            user, created = User.objects.get_or_create(
                email__iexact=email,
                defaults={"email": email, "username": email,
                          "first_name": "Admin", "last_name": "MentorMe"},
            )
            user.is_staff = True
            user.is_superuser = True
            user.is_active = True
            if created or os.environ.get("ADMIN_RESET_PASSWORD") == "1":
                user.set_password(password)
            user.save()
            self.stdout.write(self.style.SUCCESS(
                f"Administrateur {'créé' if created else 'confirmé'} : {email}"))
        else:
            self.stdout.write("ADMIN_EMAIL / ADMIN_PASSWORD absents : aucun administrateur créé.")

        if os.environ.get("SEED_DEMO") == "1":
            call_command("seed_demo")
