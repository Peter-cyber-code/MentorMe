import logging

from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework.permissions import (
    IsAuthenticated,
)
from rest_framework.response import Response

from .models import ProjectAudit
from .serializers import ProjectAuditSerializer

from .recommendations import build_recommendations
from profiles.serializers import ProfileSerializer

logger = logging.getLogger(__name__)


def get_audit_generator():
    """Choisit le fournisseur d'après settings.AUDIT_PROVIDER."""
    if settings.AUDIT_PROVIDER == "openai":
        from .services.openai_service import generate_project_audit
        return "openai", generate_project_audit

    from .services.mock_service import generate_project_audit
    return "mock", generate_project_audit

class ProjectAuditCreateView(
    generics.CreateAPIView
):

    serializer_class = ProjectAuditSerializer

    permission_classes = [
        IsAuthenticated
    ]

    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "ai_audit"

    def create(
        self,
        request,
        *args,
        **kwargs
    ):

        serializer = self.get_serializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        provider_name, generate_project_audit = get_audit_generator()

        audit = serializer.save(
            requested_by=request.user,
            status="processing",
            provider=provider_name
        )

        try:

            report = generate_project_audit(
                audit
            )

            audit.report = report
            audit.status = "completed"
            audit.error_message = ""

            audit.save(
                update_fields=[
                    "report",
                    "status",
                    "error_message",
                    "updated_at",
                ]
            )

        except Exception:
            logger.exception("Échec de l'audit %s", audit.pk)

            audit.status = "failed"
            audit.error_message = (
                "L'audit n'a pas pu être généré. Veuillez réessayer plus tard."
            )

            audit.save(
                update_fields=[
                    "status",
                    "error_message",
                    "updated_at",
                ]
            )

            return Response(
                self.get_serializer(
                    audit
                ).data,
                status=502
            )

        return Response(
            self.get_serializer(
                audit
            ).data,
            status=201
        )


# Mes audits

class MyAuditListView(
    generics.ListAPIView
):

    serializer_class = ProjectAuditSerializer

    permission_classes = [
        IsAuthenticated
    ]

    def get_queryset(self):

        return (
            ProjectAudit.objects
            .filter(
                requested_by=self.request.user
            )
            .select_related(
                "project",
                "requested_by"
            )
        )

# Detail d'un audit 

class ProjectAuditDetailView(
    generics.RetrieveAPIView
):

    serializer_class = ProjectAuditSerializer

    permission_classes = [
        IsAuthenticated
    ]

    def get_queryset(self):

        return (
            ProjectAudit.objects
            .filter(
                requested_by=self.request.user
            )
            .select_related(
                "project"
            )
        )

#Audits d'un projet 

class ProjectAuditHistoryView(
    generics.ListAPIView
):

    serializer_class = ProjectAuditSerializer

    permission_classes = [
        IsAuthenticated
    ]

    def get_queryset(self):

        return (
            ProjectAudit.objects
            .filter(
                project_id=self.kwargs[
                    "project_id"
                ],
                project__owner=self.request.user
            )
            .select_related(
                "project"
            )
        )


# Recommandations issues d'un audit terminé
class AuditRecommendationsView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        audit = get_object_or_404(
            ProjectAudit.objects.select_related("project"),
            pk=pk,
            requested_by=request.user,
        )

        if audit.status != "completed" or not audit.report:
            return Response(
                {"detail": "L'audit n'est pas terminé."},
                status=409
            )

        recommendations = build_recommendations(audit)

        payload = {
            code: [
                {
                    "score": item["score"],
                    "score_breakdown": item["score_breakdown"],
                    "reason": item["reason"],
                    "profile": ProfileSerializer(
                        item["profile"],
                        context={"request": request}
                    ).data,
                }
                for item in items
            ]
            for code, items in recommendations.items()
        }

        return Response({
            "audit_id": audit.pk,
            "overall_summary": audit.report.get("executive_summary", ""),
            "priority_actions": audit.report.get("recommendations", []),
            "recommendations": payload,
            "funding_programs": [],  # TODO : modèle FundingProgram (V2)
        })
