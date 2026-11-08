from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Project(models.Model):

    STAGE_CHOICES = [
        ("idea", "Idée"),
        ("prototype", "Prototype"),
        ("mvp", "MVP"),
        ("growth", "Croissance"),
        ("launched", "Lancé"),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField()

    sector = models.CharField(max_length=100)

    country = models.CharField(max_length=100)

    budget = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )

    stage = models.CharField(
        max_length=20,
        choices=STAGE_CHOICES,
        default="idea"
    )

    looking_for_mentor = models.BooleanField(default=False)

    looking_for_investor = models.BooleanField(default=False)

    looking_for_collaborator = models.BooleanField(default=False)

    looking_for_financial_expert = models.BooleanField(default=False)

    cover_image = models.ImageField(
        upload_to="projects/",
        blank=True,
        null=True
    )

    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="projects"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class ProjectNeed(models.Model):
    """Besoin ouvert d'un projet (ex. Expert IoT · Mission 3 mois)."""

    class Kind(models.TextChoices):
        EXPERTISE = "expertise", "Expertise"
        FUNDING = "funding", "Financement"
        COLLABORATOR = "collaborator", "Collaborateur"
        MENTOR = "mentor", "Mentor"
        OTHER = "other", "Autre"

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="needs"
    )
    kind = models.CharField(
        max_length=14,
        choices=Kind.choices,
        default=Kind.EXPERTISE
    )
    title = models.CharField(max_length=120)
    detail = models.CharField(max_length=160, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.project_id} · {self.title}"
