from django.urls import path

from .views import (
    RoleRequestListCreateView,
    ProfileListView,
    ProfileDetailView,
    MyProfileView,
    RoleListView,
    ExpertiseListView,
)


urlpatterns = [
    path(
        "role-requests/",
        RoleRequestListCreateView.as_view(),
        name="role-requests"
    ),


    path(
        "",
        ProfileListView.as_view(),
        name="profile-list"
    ),

    path(
        "me/",
        MyProfileView.as_view(),
        name="my-profile"
    ),

    path(
        "roles/",
        RoleListView.as_view(),
        name="role-list"
    ),

    path(
        "expertise/",
        ExpertiseListView.as_view(),
        name="expertise-list"
    ),

    path(
        "<int:pk>/",
        ProfileDetailView.as_view(),
        name="profile-detail"
    ),
]