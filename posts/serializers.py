from rest_framework import serializers

from projects.models import Project

from .models import (
    Post,
    PostImage,
    Comment,
)


def _author_photo(request, user):
    profile = getattr(user, "profile", None)
    if not profile or not profile.photo:
        return None
    url = profile.photo.url
    return request.build_absolute_uri(url) if request else url


def _author_headline(user):
    profile = getattr(user, "profile", None)
    if not profile:
        return ""
    return " · ".join(
        part for part in [profile.headline.strip(), profile.city.strip()] if part
    )



class PostImageSerializer(serializers.ModelSerializer):

    class Meta:
        model = PostImage
        fields = [
            "id",
            "image",
            "created_at",
        ]

        read_only_fields = [
            "id",
            "created_at",
        ]

class PostSerializer(serializers.ModelSerializer):

    images = PostImageSerializer(
        many=True,
        read_only=True
    )

    author_name = serializers.SerializerMethodField()

    author_photo = serializers.SerializerMethodField()

    author_headline = serializers.SerializerMethodField()

    project_title = serializers.CharField(
        source="project.title",
        read_only=True,
        default=None
    )

    project = serializers.PrimaryKeyRelatedField(
        queryset=Project.objects.all(),
        required=False,
        allow_null=True
    )

    hashtags = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        slug_field="name"
    )

    def get_author_name(self, obj):
        return obj.author.get_full_name() or obj.author.username

    def get_author_photo(self, obj):
        return _author_photo(self.context.get("request"), obj.author)

    def get_author_headline(self, obj):
        return _author_headline(obj.author)

    def validate_project(self, project):
        request = self.context.get("request")
        if project and request and project.owner_id != request.user.id:
            raise serializers.ValidationError(
                "Vous ne pouvez lier qu'un de vos propres projets."
            )
        return project

    liked_by_me = serializers.SerializerMethodField()

    bookmarked_by_me = serializers.SerializerMethodField()

    class Meta:
        model = Post

        fields = [
            "id",
            "author",
            "author_name",
            "author_photo",
            "author_headline",
            "title",
            "project",
            "project_title",
            "content",
            "hashtags",
            "images",
            "views_count",
            "likes_count",
            "comments_count",
            "shares_count",
            "bookmarks_count",
            "liked_by_me",
            "bookmarked_by_me",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "author",
            "hashtags",
            "views_count",
            "likes_count",
            "comments_count",
            "shares_count",
            "bookmarks_count",
        ]

    def get_liked_by_me(
        self,
        obj
    ):
        request = self.context.get("request")

        if not request:
            return False

        if not request.user.is_authenticated:
            return False

        return obj.likes.filter(
            user=request.user
        ).exists()

    def get_bookmarked_by_me(
        self,
        obj
    ):
        request = self.context.get("request")

        if not request:
            return False

        if not request.user.is_authenticated:
            return False

        return obj.bookmarked_by.filter(
            user=request.user
        ).exists()


class CommentSerializer(serializers.ModelSerializer):

    author_name = serializers.SerializerMethodField()

    author_photo = serializers.SerializerMethodField()

    def get_author_photo(self, obj):
        return _author_photo(self.context.get("request"), obj.author)

    def get_author_name(self, obj):
        return obj.author.get_full_name() or obj.author.username

    class Meta:
        model = Comment

        fields = [
            "id",
            "post",
            "author",
            "author_name",
            "author_photo",
            "content",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "author",
            "post",
        ]