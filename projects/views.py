from rest_framework import generics
from rest_framework.permissions import (
    IsAuthenticatedOrReadOnly
)

from .models import Project, ProjectNeed
from .serializers import ProjectNeedSerializer, ProjectSerializer
from .permissions import IsOwnerOrReadOnly


from rest_framework import generics
from rest_framework.filters import (
    SearchFilter,
    OrderingFilter
)

from django_filters.rest_framework import (
    DjangoFilterBackend
)



class ProjectListCreateView(
    generics.ListCreateAPIView
):
    serializer_class = ProjectSerializer

    permission_classes = [
        IsAuthenticatedOrReadOnly
    ]

    queryset = Project.objects.all()

    filter_backends = [
        DjangoFilterBackend,
        SearchFilter,
        OrderingFilter,
    ]

    search_fields = [
        "title",
        "description",
        "sector",
        "country",
    ]

    filterset_fields = [
        "sector",
        "country",
        "stage",
        "looking_for_mentor",
        "looking_for_investor",
        "looking_for_collaborator",
        "looking_for_financial_expert",
    ]

    ordering_fields = [
        "created_at",
        "budget",
    ]

    ordering = [
        "-created_at"
    ]

    def perform_create(self, serializer):
        serializer.save(
            owner=self.request.user
        )


class ProjectDetailView(
    generics.RetrieveUpdateDestroyAPIView
):

    queryset = Project.objects.all()

    serializer_class = ProjectSerializer

    permission_classes = [
        IsOwnerOrReadOnly
    ]


from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated


class ProjectNeedCreateView(generics.CreateAPIView):
    """Ajouter un besoin ouvert à l'un de ses projets."""

    serializer_class = ProjectNeedSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        project = get_object_or_404(Project, pk=self.kwargs["project_id"])
        if project.owner_id != self.request.user.id:
            raise PermissionDenied("Ce projet ne vous appartient pas.")
        serializer.save(project=project)


class ProjectNeedDeleteView(generics.DestroyAPIView):

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ProjectNeed.objects.filter(project__owner=self.request.user)
