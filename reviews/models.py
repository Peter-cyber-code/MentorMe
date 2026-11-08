from django.conf import settings
from django.core.validators import (
    MinValueValidator,
    MaxValueValidator,
)
from django.db import models

from booking.models import Booking


class Review(models.Model):

    booking = models.OneToOneField(
        Booking,
        on_delete=models.CASCADE,
        related_name="review"
    )

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reviews_written"
    )

    professional = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reviews_received"
    )

    rating = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(5),
        ]
    )

    comment = models.TextField(
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = [
            "-created_at"
        ]

    def __str__(self):
        return (
            f"{self.rating}/5 - "
            f"{self.professional}"
        )