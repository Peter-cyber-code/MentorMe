from django.contrib import admin

from .models import (
    Post,
    PostImage,
    Hashtag,
    Like,
    Comment,
    Share,
    Bookmark,
)


class PostImageInline(admin.TabularInline):
    model = PostImage
    extra = 1


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "author",
        "likes_count",
        "comments_count",
        "views_count",
        "created_at",
    )

    search_fields = (
        "content",
        "author__username",
    )

    inlines = [
        PostImageInline
    ]


admin.site.register(Hashtag)
admin.site.register(Like)
admin.site.register(Comment)
admin.site.register(Share)
admin.site.register(Bookmark)