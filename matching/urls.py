from django.urls import path

from .views import (
    MatchingProjectListView,
    ProjectMatchingPeopleView,
    MatchingMentorListView,
    MatchingExpertListView,
)


urlpatterns = [

    path(
        "projects/",
        MatchingProjectListView.as_view(),
        name="matching-projects"
    ),

    path(
        "projects/<int:project_id>/people/",
        ProjectMatchingPeopleView.as_view(),
        name="project-matching-people"
    ),

    path(
        "mentors/",
        MatchingMentorListView.as_view(),
        name="matching-mentors"
    ),

    path(
        "experts/",
        MatchingExpertListView.as_view(),
        name="matching-experts"
    ),
]