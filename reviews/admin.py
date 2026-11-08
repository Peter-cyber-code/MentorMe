from django.contrib import admin

from .models import Review


@admin.register(Review)
class ReviewAdmin(
    admin.ModelAdmin
):

    list_display = [
        "id",
        "author",
        "professional",
        "rating",
        "booking",
        "created_at",
    ]

    list_filter = [
        "rating",
        "created_at",
    ]

    search_fields = [
        "author__username",
        "professional__username",
        "comment",
    ]

    readonly_fields = [
        "created_at",
        "updated_at",
    ]

    list_select_related = [
        "author",
        "professional",
        "booking",
    ]