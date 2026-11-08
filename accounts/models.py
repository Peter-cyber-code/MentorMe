from django.db import models
from django.contrib.auth.models import AbstractUser


class CustomUser(AbstractUser):

    USER_TYPES = (
        ('PROJECT_OWNER', 'Project Owner'),
        ('MENTOR', 'Mentor'),
        ('EXPERT', 'Expert'),
        ('INVESTOR', 'Investor'),
        ('COLLABORATOR', 'Collaborator'),
    )

    email = models.EmailField(unique=True)

    user_type = models.CharField(
        max_length=20,
        choices=USER_TYPES,
        default='PROJECT_OWNER'
    )

    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )

    country = models.CharField(
        max_length=100,
        blank=True
    )

    city = models.CharField(
        max_length=100,
        blank=True
    )

    bio = models.TextField(
        blank=True
    )

    profile_picture = models.ImageField(
        upload_to='profiles/',
        blank=True,
        null=True
    )

    skills = models.TextField(
        blank=True,
        help_text="Compétences séparées par des virgules"
    )

    hourly_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    rating = models.FloatField(
        default=0
    )

    verified = models.BooleanField(
        default=False
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    USERNAME_FIELD = 'email'

    REQUIRED_FIELDS = [
        'username',
    ]

    def __str__(self):
        return self.email


class PasswordResetCode(models.Model):
    """Code à 6 chiffres envoyé par e-mail pour réinitialiser un mot de passe."""

    user = models.ForeignKey(
        "accounts.CustomUser",
        on_delete=models.CASCADE,
        related_name="reset_codes"
    )
    code_hash = models.CharField(max_length=128)
    created_at = models.DateTimeField(auto_now_add=True)
    used = models.BooleanField(default=False)
    attempts = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["-created_at"]



class SupportRequest(models.Model):
    """Message envoyé depuis « Nous contacter » (ex. mot de passe oublié)."""

    class Status(models.TextChoices):
        NEW = "new", "Nouvelle"
        HANDLED = "handled", "Traitée"

    email = models.EmailField()
    message = models.TextField()
    user = models.ForeignKey(
        "accounts.CustomUser",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="support_requests"
    )
    status = models.CharField(
        max_length=8,
        choices=Status.choices,
        default=Status.NEW
    )
    admin_note = models.TextField(blank=True)
    handled_by = models.ForeignKey(
        "accounts.CustomUser",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="handled_support_requests"
    )
    handled_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Demande d'aide"
        verbose_name_plural = "Demandes d'aide (nous contacter)"

    def __str__(self):
        return f"{self.email} ({self.status})"
