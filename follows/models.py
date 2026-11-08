from django.conf import settings
from django.db import models
from django.db.models import F, Q


class Follow(models.Model):

    follower = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="following_relations"
    )

    following = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="follower_relations"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:

        ordering = [
            "-created_at"
        ]

        constraints = [

            models.UniqueConstraint(
                fields=[
                    "follower",
                    "following"
                ],
                name="unique_follow_relationship"
            ),

            models.CheckConstraint(
                condition=~Q(
                    follower=F("following")
                ),
                name="prevent_self_follow"
            ),
        ]

    def __str__(self):

        return (
            f"{self.follower} "
            f"-> {self.following}"
        )