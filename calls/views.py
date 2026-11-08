from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import CallApplication, CallBookmark, ProjectCall
from .serializers import CallApplicationSerializer, ProjectCallSerializer


def open_calls():
    """Appels publiés et dont la date limite n'est pas dépassée."""
    return ProjectCall.objects.filter(is_published=True).filter(
        Q(deadline__isnull=True) | Q(deadline__gte=timezone.localdate())
    )


class CallListView(generics.ListAPIView):

    serializer_class = ProjectCallSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = open_calls()
        category = self.request.query_params.get("category")
        if category:
            qs = qs.filter(category=category)
        return qs


class SavedCallListView(generics.ListAPIView):

    serializer_class = ProjectCallSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return open_calls().filter(bookmarks__user=self.request.user)


class CallSaveView(APIView):
    """Enregistrer / retirer un appel de ses favoris."""

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        call = get_object_or_404(open_calls(), pk=pk)
        bookmark, created = CallBookmark.objects.get_or_create(
            user=request.user, call=call
        )
        if not created:
            bookmark.delete()
        return Response({"saved": created})


class CallApplyView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        call = get_object_or_404(open_calls(), pk=pk)

        if CallApplication.objects.filter(user=request.user, call=call).exists():
            return Response(
                {"detail": "Vous avez déjà postulé à cet appel."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = CallApplicationSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user, call=call)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
