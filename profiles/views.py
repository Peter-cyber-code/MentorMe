from rest_framework import generics
from rest_framework.filters import (
    SearchFilter,
    OrderingFilter,
)
from rest_framework.parsers import (
    MultiPartParser,
    FormParser,
    JSONParser,
)
from rest_framework.permissions import (
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
)

from .models import (
    Profile,
    Role,
    Expertise,
)

from .serializers import (
    ProfileSerializer,
    RoleSerializer,
    ExpertiseSerializer,
)

from .permissions import (
    IsProfileOwnerOrReadOnly,
)

from .pagination import (
    ProfilePagination,
)

class ProfileListView(
    generics.ListAPIView
):

    serializer_class = ProfileSerializer

    permission_classes = [
        IsAuthenticatedOrReadOnly
    ]

    pagination_class = ProfilePagination

    filter_backends = [
        SearchFilter,
        OrderingFilter,
    ]

    search_fields = [
        "user__username",
        "user__first_name",
        "user__last_name",
        "bio",
        "country",
        "city",
        "expertise__name",
    ]

    ordering_fields = [
        "created_at",
        "session_price",
    ]

    ordering = [
        "-created_at"
    ]

    def get_queryset(self):

        queryset = (
            Profile.objects
            .select_related("user")
            .prefetch_related(
                "roles",
                "expertise"
            )
        )

        role = self.request.query_params.get(
            "role"
        )

        expertise = self.request.query_params.get(
            "expertise"
        )

        available = self.request.query_params.get(
            "available"
        )

        country = self.request.query_params.get(
            "country"
        )

        if role:
            codes = [c.strip() for c in role.split(",") if c.strip()]
            queryset = queryset.filter(
                roles__code__in=codes
            ).distinct()

        if expertise:

            queryset = queryset.filter(
                expertise__name__iexact=expertise
            )

        if country:

            queryset = queryset.filter(
                country__iexact=country
            )

        if available is not None:

            value = available.lower()

            if value in [
                "true",
                "1",
                "yes"
            ]:

                queryset = queryset.filter(
                    is_available=True
                )

            elif value in [
                "false",
                "0",
                "no"
            ]:

                queryset = queryset.filter(
                    is_available=False
                )

        return queryset.distinct()


class ProfileDetailView(
    generics.RetrieveAPIView
):

    queryset = (
        Profile.objects
        .select_related("user")
        .prefetch_related(
            "roles",
            "expertise"
        )
    )

    serializer_class = ProfileSerializer

    permission_classes = [
        IsAuthenticatedOrReadOnly
    ]


class MyProfileView(
    generics.RetrieveUpdateAPIView
):

    serializer_class = ProfileSerializer

    permission_classes = [
        IsAuthenticated
    ]

    parser_classes = [
        MultiPartParser,
        FormParser,
        JSONParser,
    ]

    def get_object(self):

        profile, created = (
            Profile.objects.get_or_create(
                user=self.request.user
            )
        )

        return profile

class RoleListView(
    generics.ListAPIView
):

    queryset = Role.objects.all()

    serializer_class = RoleSerializer

    permission_classes = [
        IsAuthenticatedOrReadOnly
    ]

class ExpertiseListView(
    generics.ListAPIView
):

    queryset = Expertise.objects.all()

    serializer_class = ExpertiseSerializer

    permission_classes = [
        IsAuthenticatedOrReadOnly
    ]



from rest_framework import generics as _generics
from rest_framework.permissions import IsAuthenticated as _IsAuthenticated

from .models import RoleRequest
from .serializers import RoleRequestSerializer


class RoleRequestListCreateView(_generics.ListCreateAPIView):
    """Mes demandes de rôle (mentor, expert, investisseur) et nouvelle demande."""

    serializer_class = RoleRequestSerializer
    permission_classes = [_IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        return RoleRequest.objects.filter(
            user=self.request.user
        ).select_related("role")
