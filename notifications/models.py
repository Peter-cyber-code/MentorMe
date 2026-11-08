from django.conf import settings
from django.db import models


class Notification(models.Model):

    TYPE_CHOICES = [
        (
            "message",
            "Nouveau message"
        ),
        (
            "booking_created",
            "Nouvelle réservation"
        ),
        (
            "booking_confirmed",
            "Réservation confirmée"
        ),
        (
            "booking_cancelled",
            "Réservation annulée"
        ),
        (
            "booking_rejected",
            "Réservation refusée"
        ),
        (
            "booking_completed",
            "Session terminée"
        ),
        (
            "role_approved",
            "Rôle validé"
        ),
        (
            "role_rejected",
            "Rôle refusé"
        ),
        (
            "review",
            "Nouvel avis"
        ),
    ]

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications"
    )

    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sent_notifications"
    )

    notification_type = models.CharField(
        max_length=30,
        choices=TYPE_CHOICES
    )

    title = models.CharField(
        max_length=150
    )

    message = models.TextField(
        blank=True
    )

    resource_type = models.CharField(
        max_length=50,
        blank=True
    )

    resource_id = models.PositiveBigIntegerField(
        null=True,
        blank=True
    )

    is_read = models.BooleanField(
        default=False
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = [
            "-created_at"
        ]

        indexes = [
            models.Index(
                fields=[
                    "recipient",
                    "is_read",
                    "-created_at",
                ]
            )
        ]

    def __str__(self):
        return (
            f"{self.recipient} - "
            f"{self.title}"
        )