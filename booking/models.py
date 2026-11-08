from django.conf import settings
from django.db import models
from django.core.exceptions import ValidationError


class Availability(models.Model):

    provider = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="availabilities"
    )

    date = models.DateField()

    start_time = models.TimeField()

    end_time = models.TimeField()

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = [
            "date",
            "start_time"
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "provider",
                    "date",
                    "start_time",
                    "end_time"
                ],
                name="unique_provider_availability"
            )
        ]

    def clean(self):

        if self.start_time >= self.end_time:
            raise ValidationError(
                "L'heure de fin doit être après l'heure de début."
            )

    def __str__(self):
        return (
            f"{self.provider} - "
            f"{self.date} "
            f"{self.start_time}"
        )


class Booking(models.Model):

    STATUS_CHOICES = [
        ("PENDING", "En attente"),
        ("CONFIRMED", "Confirmée"),
        ("COMPLETED", "Terminée"),
        ("CANCELLED", "Annulée"),
        ("REJECTED", "Refusée"),
    ]

    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="bookings_made"
    )

    provider = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="bookings_received"
    )

    availability = models.ForeignKey(
        Availability,
        on_delete=models.PROTECT,
        related_name="bookings"
    )

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="PENDING"
    )

    message = models.TextField(
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return (
            f"{self.client} → "
            f"{self.provider} "
            f"({self.status})"
        )