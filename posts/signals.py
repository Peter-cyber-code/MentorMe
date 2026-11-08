from django.db.models.signals import (
    post_save,
    post_delete,
)
from django.dispatch import receiver
from django.db.models import F

from .models import (
    Like,
    Comment,
    Share,
    Bookmark,
    Post,
)


# =========================
# LIKES
# =========================

@receiver(post_save, sender=Like)
def increment_like_count(
    sender,
    instance,
    created,
    **kwargs
):
    if created:
        Post.objects.filter(
            pk=instance.post_id
        ).update(
            likes_count=F("likes_count") + 1
        )


@receiver(post_delete, sender=Like)
def decrement_like_count(
    sender,
    instance,
    **kwargs
):
    post = Post.objects.filter(
        pk=instance.post_id
    ).first()

    if post and post.likes_count > 0:
        Post.objects.filter(
            pk=instance.post_id
        ).update(
            likes_count=F("likes_count") - 1
        )


# =========================
# COMMENTS
# =========================

@receiver(post_save, sender=Comment)
def increment_comment_count(
    sender,
    instance,
    created,
    **kwargs
):
    if created:
        Post.objects.filter(
            pk=instance.post_id
        ).update(
            comments_count=F("comments_count") + 1
        )


@receiver(post_delete, sender=Comment)
def decrement_comment_count(
    sender,
    instance,
    **kwargs
):
    post = Post.objects.filter(
        pk=instance.post_id
    ).first()

    if post and post.comments_count > 0:
        Post.objects.filter(
            pk=instance.post_id
        ).update(
            comments_count=F("comments_count") - 1
        )


# =========================
# SHARES
# =========================

@receiver(post_save, sender=Share)
def increment_share_count(
    sender,
    instance,
    created,
    **kwargs
):
    if created:
        Post.objects.filter(
            pk=instance.original_post_id
        ).update(
            shares_count=F("shares_count") + 1
        )


@receiver(post_delete, sender=Share)
def decrement_share_count(
    sender,
    instance,
    **kwargs
):
    post = Post.objects.filter(
        pk=instance.original_post_id
    ).first()

    if post and post.shares_count > 0:
        Post.objects.filter(
            pk=instance.original_post_id
        ).update(
            shares_count=F("shares_count") - 1
        )


# =========================
# BOOKMARKS
# =========================

@receiver(post_save, sender=Bookmark)
def increment_bookmark_count(
    sender,
    instance,
    created,
    **kwargs
):
    if created:
        Post.objects.filter(
            pk=instance.post_id
        ).update(
            bookmarks_count=F("bookmarks_count") + 1
        )


@receiver(post_delete, sender=Bookmark)
def decrement_bookmark_count(
    sender,
    instance,
    **kwargs
):
    post = Post.objects.filter(
        pk=instance.post_id
    ).first()

    if post and post.bookmarks_count > 0:
        Post.objects.filter(
            pk=instance.post_id
        ).update(
            bookmarks_count=F("bookmarks_count") - 1
        )