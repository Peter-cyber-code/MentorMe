from django.contrib.auth import get_user_model
from django.db.models import Avg, Count

from rest_framework import generics
from rest_framework.permissions import (
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Review

from .serializers import (
    ReviewSerializer,
)

from .permissions import (
    IsReviewAuthorOrReadOnly,
)

from .pagination import (
    ReviewPagination,
)


User = get_user_model()


class ReviewCreateView(
    generics.CreateAPIView
):

    queryset = Review.objects.all()

    serializer_class = ReviewSerializer

    permission_classes = [
        IsAuthenticated
    ]

class ProfessionalReviewListView(
    generics.ListAPIView
):

    serializer_class = ReviewSerializer

    permission_classes = [
        IsAuthenticatedOrReadOnly
    ]

    pagination_class = ReviewPagination

    def get_queryset(self):

        return (
            Review.objects
            .filter(
                professional_id=self.kwargs[
                    "user_id"
                ]
            )
            .select_related(
                "author",
                "professional",
                "booking"
            )
            .order_by(
                "-created_at"
            )
        )

class MyReviewListView(
    generics.ListAPIView
):

    serializer_class = ReviewSerializer

    permission_classes = [
        IsAuthenticated
    ]

    pagination_class = ReviewPagination

    def get_queryset(self):

        return (
            Review.objects
            .filter(
                author=self.request.user
            )
            .select_related(
                "author",
                "professional",
                "booking"
            )
            .order_by(
                "-created_at"
            )
        )


class ReviewDetailView(
    generics.RetrieveUpdateDestroyAPIView
):

    queryset = (
        Review.objects
        .select_related(
            "author",
            "professional",
            "booking"
        )
    )

    serializer_class = ReviewSerializer

    permission_classes = [
        IsAuthenticatedOrReadOnly,
        IsReviewAuthorOrReadOnly,
    ]


class ProfessionalRatingView(
    APIView
):

    permission_classes = [
        IsAuthenticatedOrReadOnly
    ]

    def get(
        self,
        request,
        user_id
    ):

        reviews = Review.objects.filter(
            professional_id=user_id
        )

        stats = reviews.aggregate(
            average_rating=Avg(
                "rating"
            ),
            reviews_count=Count(
                "id"
            )
        )

        average = (
            stats["average_rating"]
            or 0
        )

        return Response(
            {
                "average_rating": round(
                    average,
                    1
                ),
                "reviews_count":
                    stats["reviews_count"],
            }
        )