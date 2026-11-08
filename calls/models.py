from django.conf import settings
from django.db import models


class ProjectCall(models.Model):
    """Appel à projets publié par l'administration (concours, subvention…)."""

    class Category(models.TextChoices):
        CONTEST = "concours", "Concours"
        GRANT = "subvention", "Subvention"
        ACCELERATOR = "accelerateur", "Accélérateur"
        LOAN = "pret", "Prêt"
        OTHER = "autre", "Autre"

    title = models.CharField(max_length=200)
    organization = models.CharField(max_length=150)
    category = models.CharField(
        max_length=14,
        choices=Category.choices,
        default=Category.CONTEST
    )
    description = models.TextField(blank=True)
    deadline = models.DateField(null=True, blank=True)
    apply_url = models.URLField(
        blank=True,
        help_text="Lien officiel pour postuler (facultatif)"
    )
    is_published = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="published_calls"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["deadline", "-created_at"]
        verbose_name = "Appel à projets"
        verbose_name_plural = "Appels à projets"

    def __str__(self):
        return self.title


class CallBookmark(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="call_bookmarks"
    )
    call = models.ForeignKey(
        ProjectCall,
        on_delete=models.CASCADE,
        related_name="bookmarks"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "call"],
                name="unique_call_bookmark"
            )
        ]


class CallApplication(models.Model):
    """Candidature d'un utilisateur (avec l'un de ses projets) à un appel."""

    class Status(models.TextChoices):
        SUBMITTED = "submitted", "Envoyée"
        SHORTLISTED = "shortlisted", "Présélectionnée"
        REJECTED = "rejected", "Non retenue"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="call_applications"
    )
    call = models.ForeignKey(
        ProjectCall,
        on_delete=models.CASCADE,
        related_name="applications"
    )
    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="call_applications"
    )
    message = models.TextField(blank=True)
    status = models.CharField(
        max_length=12,
        choices=Status.choices,
        default=Status.SUBMITTED
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Candidature à un appel"
        verbose_name_plural = "Candidatures aux appels"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "call"],
                name="unique_call_application"
            )
        ]
