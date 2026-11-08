from rest_framework import serializers

from .models import ProjectAudit


class ProjectAuditSerializer(
    serializers.ModelSerializer
):

    project_title = serializers.CharField(
        source="project.title",
        read_only=True
    )

    class Meta:
        model = ProjectAudit

        fields = [
            "id",
            "project",
            "project_title",

            "problem",
            "solution",
            "target_customers",
            "business_model",
            "competitors",
            "team",
            "funding_need",

            "status",
            "provider",
            "report",
            "error_message",

            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "project_title",
            "status",
            "provider",
            "report",
            "error_message",
            "created_at",
            "updated_at",
        ]


    def validate_project(self, project):

        request = self.context.get("request")

        if (
            not request
            or not request.user.is_authenticated
        ):
            raise serializers.ValidationError(
                "Authentification requise."
            )

        if project.owner != request.user:

            raise serializers.ValidationError(
                "Vous ne pouvez auditer que vos propres projets."
            )

        return project