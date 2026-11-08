from django.conf import settings
from django.db import models


class Role(models.Model):

    ROLE_CHOICES = [
        ("project_owner", "Porteur de projet"),
        ("mentor", "Mentor"),
        ("investor", "Investisseur"),
        ("financial_expert", "Expert financier"),
        ("marketing_expert", "Expert marketing"),
        ("legal_expert", "Expert juridique"),
        ("collaborator", "Collaborateur"),
    ]

    code = models.CharField(
        max_length=50,
        choices=ROLE_CHOICES,
        unique=True
    )

    def __str__(self):
        return self.get_code_display()


class Expertise(models.Model):

    name = models.CharField(
        max_length=100,
        unique=True
    )

    def __str__(self):
        return self.name


class Profile(models.Model):

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile"
    )

    photo = models.ImageField(
        upload_to="profiles/",
        null=True,
        blank=True
    )

    headline = models.CharField(
        max_length=120,
        blank=True,
        help_text="Ex. : Fondatrice · Kër Care"
    )

    bio = models.TextField(
        blank=True
    )

    country = models.CharField(
        max_length=100,
        blank=True
    )

    city = models.CharField(
        max_length=100,
        blank=True
    )

    roles = models.ManyToManyField(
        Role,
        related_name="profiles",
        blank=True
    )

    expertise = models.ManyToManyField(
        Expertise,
        related_name="profiles",
        blank=True
    )

    session_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )

    session_duration = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Durée en minutes"
    )

    is_available = models.BooleanField(
        default=True
    )

    is_verified = models.BooleanField(
        default=False
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return f"Profil de {self.user}"


class RoleRequest(models.Model):
    """Demande d'un utilisateur pour devenir mentor, expert ou investisseur."""

    class Status(models.TextChoices):
        PENDING = "pending", "En attente"
        APPROVED = "approved", "Validée"
        REJECTED = "rejected", "Refusée"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="role_requests"
    )
    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        related_name="requests"
    )
    message = models.TextField(
        help_text="Présentation et justification de la demande"
    )
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING
    )
    admin_note = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_role_requests"
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Demande de rôle"
        verbose_name_plural = "Demandes de rôle (mentor, expert…)"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "role"],
                condition=models.Q(status="pending"),
                name="one_pending_request_per_role",
            )
        ]

    def __str__(self):
        return f"{self.user} → {self.role.code} ({self.status})"
