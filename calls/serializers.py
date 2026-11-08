from rest_framework import serializers

from projects.models import Project

from .models import CallApplication, CallBookmark, ProjectCall


class ProjectCallSerializer(serializers.ModelSerializer):

    category_label = serializers.CharField(
        source="get_category_display",
        read_only=True
    )
    saved = serializers.SerializerMethodField()
    applied = serializers.SerializerMethodField()

    class Meta:
        model = ProjectCall
        fields = [
            "id",
            "title",
            "organization",
            "category",
            "category_label",
            "description",
            "deadline",
            "apply_url",
            "saved",
            "applied",
        ]

    def _user(self):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        return user if user and user.is_authenticated else None

    def get_saved(self, obj):
        user = self._user()
        return bool(user) and CallBookmark.objects.filter(user=user, call=obj).exists()

    def get_applied(self, obj):
        user = self._user()
        return bool(user) and CallApplication.objects.filter(user=user, call=obj).exists()


class CallApplicationSerializer(serializers.ModelSerializer):

    project = serializers.PrimaryKeyRelatedField(
        queryset=Project.objects.all(),
        required=False,
        allow_null=True
    )

    class Meta:
        model = CallApplication
        fields = ["id", "call", "project", "message", "status", "created_at"]
        read_only_fields = ["call", "status", "created_at"]

    def validate_project(self, project):
        user = self.context["request"].user
        if project and project.owner_id != user.id:
            raise serializers.ValidationError(
                "Vous ne pouvez candidater qu'avec l'un de vos projets."
            )
        return project
