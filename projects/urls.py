from django.urls import path

from .views import (
    ProjectListCreateView,
    ProjectDetailView,
    ProjectNeedCreateView,
    ProjectNeedDeleteView,
)

urlpatterns = [

    path(
        "",
        ProjectListCreateView.as_view(),
        name="project-list"
    ),

    path(
        "<int:project_id>/needs/",
        ProjectNeedCreateView.as_view(),
        name="project-need-create"
    ),

    path(
        "needs/<int:pk>/",
        ProjectNeedDeleteView.as_view(),
        name="project-need-delete"
    ),

    path(
        "<int:pk>/",
        ProjectDetailView.as_view(),
        name="project-detail"
    ),
]