from django.db.models import Q

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from projects.models import Project
from projects.serializers import ProjectSerializer

from profiles.models import Profile
from profiles.serializers import ProfileSerializer


class MatchingProjectListView(
    generics.ListAPIView
):

    serializer_class = ProjectSerializer

    permission_classes = [
        IsAuthenticated
    ]

    def get_queryset(self):

        user = self.request.user

        profile = getattr(
            user,
            "profile",
            None
        )

        if not profile:

            return Project.objects.none()

        role_codes = set(
            profile.roles.values_list(
                "code",
                flat=True
            )
        )

        query = Q()

        if "mentor" in role_codes:

            query |= Q(
                looking_for_mentor=True
            )

        if "investor" in role_codes:

            query |= Q(
                looking_for_investor=True
            )

        if "collaborator" in role_codes:

            query |= Q(
                looking_for_collaborator=True
            )

        if "financial_expert" in role_codes:

            query |= Q(
                looking_for_financial_expert=True
            )

        if not query:

            return Project.objects.none()

        queryset = (
            Project.objects
            .filter(query)
            .select_related("owner")
            .distinct()
        )

        expertise_names = list(
            profile.expertise.values_list(
                "name",
                flat=True
            )
        )

        if expertise_names:

            sector_query = Q()

            for expertise in expertise_names:

                sector_query |= Q(
                    sector__iexact=expertise
                )

            matched_sector = queryset.filter(
                sector_query
            )

            if matched_sector.exists():

                queryset = matched_sector

        return queryset.order_by(
            "-created_at"
        )


class ProjectMatchingPeopleView(
    generics.ListAPIView
):

    serializer_class = ProfileSerializer

    permission_classes = [
        IsAuthenticated
    ]

    def get_queryset(self):

        project_id = self.kwargs[
            "project_id"
        ]

        try:

            project = Project.objects.get(
                pk=project_id
            )

        except Project.DoesNotExist:

            return Profile.objects.none()

        query = Q()

        if project.looking_for_mentor:

            query |= Q(
                roles__code="mentor"
            )

        if project.looking_for_investor:

            query |= Q(
                roles__code="investor"
            )

        if project.looking_for_collaborator:

            query |= Q(
                roles__code="collaborator"
            )

        if project.looking_for_financial_expert:

            query |= Q(
                roles__code="financial_expert"
            )

        if not query:

            return Profile.objects.none()

        queryset = (
            Profile.objects
            .filter(query)
            .exclude(
                user=project.owner
            )
            .select_related("user")
            .prefetch_related(
                "roles",
                "expertise"
            )
            .distinct()
        )

        return queryset


class MatchingMentorListView(
    generics.ListAPIView
):

    serializer_class = ProfileSerializer

    permission_classes = [
        IsAuthenticated
    ]

    def get_queryset(self):

        queryset = (
            Profile.objects
            .filter(
                roles__code="mentor",
                is_available=True
            )
            .select_related("user")
            .prefetch_related(
                "roles",
                "expertise"
            )
            .distinct()
        )

        expertise = (
            self.request.query_params.get(
                "expertise"
            )
        )

        if expertise:

            queryset = queryset.filter(
                expertise__name__iexact=expertise
            )

        return queryset


class MatchingExpertListView(
    generics.ListAPIView
):

    serializer_class = ProfileSerializer

    permission_classes = [
        IsAuthenticated
    ]

    def get_queryset(self):

        queryset = (
            Profile.objects
            .filter(
                Q(
                    roles__code="financial_expert"
                )
                |
                Q(
                    roles__code="marketing_expert"
                )
                |
                Q(
                    roles__code="legal_expert"
                ),
                is_available=True
            )
            .select_related("user")
            .prefetch_related(
                "roles",
                "expertise"
            )
            .distinct()
        )

        expertise = (
            self.request.query_params.get(
                "expertise"
            )
        )

        if expertise:

            queryset = queryset.filter(
                expertise__name__iexact=expertise
            )

        return queryset