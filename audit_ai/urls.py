from django.urls import path

from .views import (
    AuditRecommendationsView,
    ProjectAuditCreateView,
    ProjectAuditDetailView,
    ProjectAuditHistoryView,
    MyAuditListView,
)


urlpatterns = [

    path(
        "",
        ProjectAuditCreateView.as_view(),
        name="audit-create"
    ),

    path(
        "mine/",
        MyAuditListView.as_view(),
        name="my-audits"
    ),

    path(
        "projects/<int:project_id>/",
        ProjectAuditHistoryView.as_view(),
        name="project-audit-history"
    ),

    path(
        "<int:pk>/recommendations/",
        AuditRecommendationsView.as_view(),
        name="audit-recommendations"
    ),

    path(
        "<int:pk>/",
        ProjectAuditDetailView.as_view(),
        name="audit-detail"
    ),
]