from django.db.models import Avg
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from notifications.services import create_notification

from .models import Review


def _refresh_rating(professional_id):
    """Recalcule la note moyenne stockée sur l'utilisateur."""
    from django.contrib.auth import get_user_model

    average = (
        Review.objects
        .filter(professional_id=professional_id)
        .aggregate(avg=Avg("rating"))["avg"]
    )
    get_user_model().objects.filter(pk=professional_id).update(
        rating=round(average, 2) if average is not None else 0
    )


@receiver(post_save, sender=Review)
def review_saved(sender, instance, created, **kwargs):
    _refresh_rating(instance.professional_id)

    if created:
        create_notification(
            recipient=instance.professional,
            sender=instance.author,
            notification_type="review",
            title="Nouvel avis reçu",
            message=f"Note : {instance.rating}/5",
            resource_type="review",
            resource_id=instance.id,
        )


@receiver(post_delete, sender=Review)
def review_deleted(sender, instance, **kwargs):
    _refresh_rating(instance.professional_id)
