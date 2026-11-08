"""Remplit la base avec des données de démonstration (idempotent).

    python manage.py seed_demo

Comptes créés (mot de passe commun : Demo#2026pass) :
  mentors : mariam.kone@demo.mentorme, yann.moukoko@demo.mentorme, fatou.diallo@demo.mentorme
  porteurs : awa.traore@demo.mentorme, ibrahima.diop@demo.mentorme
"""
from datetime import time, timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from booking.models import Availability
from calls.models import ProjectCall
from posts.models import Hashtag, Post
from profiles.models import Expertise, Role
from projects.models import Project, ProjectNeed

PASSWORD = "Demo#2026pass"

EXPERTISES = ["Finance", "Business plan", "Marketing", "Juridique", "Agriculture", "Santé"]

MENTORS = [
    ("Mariam", "Koné", "mariam.kone", "Abidjan", "Côte d'Ivoire", "Stratégie financière",
     "Dix ans en finance d'entreprise : plans de financement, relations bancaires, levées d'amorçage.",
     25000, "Finance", 4.9),
    ("Yann", "Moukoko", "yann.moukoko", "Douala", "Cameroun", "Business plan & levée",
     "J'aide les fondateurs à structurer leur business plan et préparer leur première levée.",
     20000, "Business plan", 4.8),
    ("Fatou", "Diallo", "fatou.diallo", "Dakar", "Sénégal", "Marketing & croissance",
     "Positionnement, acquisition de clients et lancement de produits en Afrique de l'Ouest.",
     15000, "Marketing", 4.7),
]

OWNERS = [
    ("Awa", "Traoré", "awa.traore", "Abidjan", "Côte d'Ivoire", "Fondatrice · Kër Care",
     "Je développe des solutions de santé de proximité accessibles aux femmes et aux familles."),
    ("Ibrahima", "Diop", "ibrahima.diop", "Dakar", "Sénégal", "Fondateur · AgriPulse",
     "Je rends l'irrigation intelligente abordable pour les petites exploitations."),
]


class Command(BaseCommand):
    help = "Crée des mentors, projets, publications, appels à projets et créneaux de démonstration."

    def _user(self, first, last, slug, city, country, headline, bio):
        User = get_user_model()
        email = f"{slug}@demo.mentorme"
        user, created = User.objects.get_or_create(
            email=email,
            defaults={"username": email, "first_name": first, "last_name": last},
        )
        if created:
            user.set_password(PASSWORD)
            user.save()
        profile = user.profile
        profile.city, profile.country = city, country
        profile.headline, profile.bio = headline, bio
        profile.save()
        return user

    def handle(self, *args, **options):
        roles = {code: Role.objects.get_or_create(code=code)[0]
                 for code in ["project_owner", "mentor"]}
        expertise = {n: Expertise.objects.get_or_create(name=n)[0] for n in EXPERTISES}

        # --- mentors vérifiés ---------------------------------------------
        mentors = []
        for first, last, slug, city, country, headline, bio, price, exp, rating in MENTORS:
            user = self._user(first, last, slug, city, country, headline, bio)
            profile = user.profile
            profile.is_verified = True
            profile.is_available = True
            profile.session_price = price
            profile.session_duration = 60
            profile.save()
            profile.roles.add(roles["mentor"])
            profile.expertise.add(expertise[exp])
            type(user).objects.filter(pk=user.pk).update(rating=rating)
            mentors.append(user)

        # --- porteurs de projet --------------------------------------------
        owners = {}
        for first, last, slug, city, country, headline, bio in OWNERS:
            user = self._user(first, last, slug, city, country, headline, bio)
            user.profile.roles.add(roles["project_owner"])
            owners[slug] = user

        projects = {}
        specs = [
            ("awa.traore", "Kër Care", "Santé", "Côte d'Ivoire", "prototype", 20000000,
             "Des centres de santé communautaires proches des familles, avec suivi maternel et pédiatrique.",
             [("expertise", "Expert santé communautaire", "Mission · 3 mois"),
              ("funding", "Financement pilote", "Objectif · 20 000 000 FCFA")]),
            ("ibrahima.diop", "AgriPulse", "Agriculture", "Sénégal", "prototype", 10000000,
             "Une solution d'irrigation intelligente, abordable et adaptée aux petites exploitations d'Afrique de l'Ouest.",
             [("expertise", "Expert IoT", "Mission · 3 mois"),
              ("funding", "Financement pilote", "Objectif · 10 000 000 FCFA")]),
        ]
        for slug, title, sector, country, stage, budget, desc, needs in specs:
            project, _ = Project.objects.get_or_create(
                owner=owners[slug], title=title,
                defaults={"description": desc, "sector": sector, "country": country,
                          "stage": stage, "budget": budget,
                          "looking_for_mentor": True, "looking_for_investor": True,
                          "looking_for_financial_expert": True},
            )
            for kind, ntitle, detail in needs:
                ProjectNeed.objects.get_or_create(
                    project=project, title=ntitle, defaults={"kind": kind, "detail": detail})
            projects[slug] = project

        # --- publications ---------------------------------------------------
        posts = [
            ("awa.traore", "Kër Care ouvre son premier centre pilote.",
             "Nous préparons une levée de fonds pour lancer notre service de santé communautaire.",
             ["objectif_financement", "stade_prototype"]),
            ("ibrahima.diop", "",
             "Nous automatisons l'irrigation des petites exploitations. Nous cherchons un expert IoT pour finaliser notre premier pilote au Sénégal.",
             ["objectif_collaborateur", "stade_prototype"]),
        ]
        for slug, title, content, tags in posts:
            post, created = Post.objects.get_or_create(
                author=owners[slug], content=content,
                defaults={"title": title, "project": projects[slug]})
            if created:
                for t in tags:
                    post.hashtags.add(Hashtag.objects.get_or_create(name=t)[0])

        # --- appels à projets (publiés par l'administration) ---------------
        today = timezone.localdate()
        calls = [
            ("Fonds d'amorçage pour l'innovation durable", "Fondation Horizon Afrique", "subvention", 45,
             "Subvention d'amorçage pour les projets à impact environnemental et social."),
            ("Prix Jeune Entrepreneur Francophone", "Africa Forward", "concours", 60,
             "Concours ouvert aux entrepreneurs francophones de moins de 35 ans."),
            ("Programme d'accélération AgriTech", "AgriTech Hub", "accelerateur", 90,
             "Six mois d'accompagnement, de mentorat et de mise en relation avec des investisseurs."),
        ]
        for title, org, cat, days, desc in calls:
            ProjectCall.objects.get_or_create(
                title=title, organization=org,
                defaults={"category": cat, "description": desc,
                          "deadline": today + timedelta(days=days)})

        # --- créneaux des mentors (5 prochains jours) -----------------------
        for mentor in mentors:
            for d in range(1, 6):
                day = today + timedelta(days=d)
                for start, end in [(time(10), time(11)), (time(14), time(15))]:
                    Availability.objects.get_or_create(
                        provider=mentor, date=day, start_time=start, end_time=end)

        self.stdout.write(self.style.SUCCESS(
            f"Données de démonstration prêtes. Mot de passe commun : {PASSWORD}"))
