from rest_framework import serializers
from .models import Project, ProjectNeed


class ProjectNeedSerializer(serializers.ModelSerializer):

    class Meta:
        model = ProjectNeed
        fields = ["id", "kind", "title", "detail"]


class ProjectSerializer(serializers.ModelSerializer):

    needs = ProjectNeedSerializer(many=True, read_only=True)

    owner_photo = serializers.SerializerMethodField()

    owner_headline = serializers.SerializerMethodField()


    owner_name = serializers.SerializerMethodField()

    class Meta:
        model = Project

        fields = [
            "id",
            "title",
            "description",
            "sector",
            "country",
            "budget",
            "stage",
            "looking_for_mentor",
            "looking_for_investor",
            "looking_for_collaborator",
            "looking_for_financial_expert",
            "cover_image",
            "owner",
            "owner_name",
            "owner_photo",
            "owner_headline",
            "needs",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "owner",
            "owner_name",
            "created_at",
            "updated_at",
        ]

    def validate_cover_image(self, value):
        if value and value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError(
                "L'image de couverture dépasse 5 Mo."
            )
        return value

    def get_owner_photo(self, obj):
        profile = getattr(obj.owner, "profile", None)
        if not profile or not profile.photo:
            return None
        request = self.context.get("request")
        url = profile.photo.url
        return request.build_absolute_uri(url) if request else url

    def get_owner_headline(self, obj):
        profile = getattr(obj.owner, "profile", None)
        return profile.headline if profile else ""

    def get_owner_name(self, obj):
        return obj.owner.get_full_name() or obj.owner.username
