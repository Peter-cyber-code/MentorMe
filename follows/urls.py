from django.urls import path

from .views import (
    ToggleFollowView,
    FollowersListView,
    FollowingListView,
    FollowStatusView,
    MyNetworkView,
)


urlpatterns = [

    path(
        "toggle/<int:user_id>/",
        ToggleFollowView.as_view(),
        name="toggle-follow"
    ),

    path(
        "users/<int:user_id>/followers/",
        FollowersListView.as_view(),
        name="followers-list"
    ),

    path(
        "users/<int:user_id>/following/",
        FollowingListView.as_view(),
        name="following-list"
    ),

    path(
        "users/<int:user_id>/status/",
        FollowStatusView.as_view(),
        name="follow-status"
    ),

    path(
        "me/",
        MyNetworkView.as_view(),
        name="my-network"
    ),
]