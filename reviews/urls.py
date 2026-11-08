from django.urls import path

from .views import (
    ReviewCreateView,
    ProfessionalReviewListView,
    MyReviewListView,
    ReviewDetailView,
    ProfessionalRatingView,
)


urlpatterns = [

    path(
        "",
        ReviewCreateView.as_view(),
        name="review-create"
    ),

    path(
        "mine/",
        MyReviewListView.as_view(),
        name="my-reviews"
    ),

    path(
        "professionals/<int:user_id>/",
        ProfessionalReviewListView.as_view(),
        name="professional-reviews"
    ),

    path(
        "professionals/<int:user_id>/rating/",
        ProfessionalRatingView.as_view(),
        name="professional-rating"
    ),

    path(
        "<int:pk>/",
        ReviewDetailView.as_view(),
        name="review-detail"
    ),
]