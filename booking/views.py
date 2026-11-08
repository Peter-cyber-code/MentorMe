from datetime import datetime

from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from notifications.services import create_notification
from profiles.models import Profile
from profiles.roles import is_provider

from .models import Availability, Booking
from .permissions import IsMentorOrExpert
from .serializers import AvailabilitySerializer, BookingSerializer


ACTIVE_STATUSES = ["PENDING", "CONFIRMED", "COMPLETED"]


def _error(detail, code=status.HTTP_400_BAD_REQUEST):
    return Response({"detail": detail}, status=code)


def _slot_start(availability):
    return timezone.make_aware(
        datetime.combine(availability.date, availability.start_time)
    )


class MyAvailabilityListCreateView(generics.ListCreateAPIView):

    serializer_class = AvailabilitySerializer
    permission_classes = [IsAuthenticated, IsMentorOrExpert]

    def get_queryset(self):
        return Availability.objects.filter(provider=self.request.user)

    def perform_create(self, serializer):
        serializer.save(provider=self.request.user)


class MyAvailabilityDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Modifier ou supprimer un de ses créneaux (si non réservé)."""

    serializer_class = AvailabilitySerializer
    permission_classes = [IsAuthenticated, IsMentorOrExpert]

    def get_queryset(self):
        return Availability.objects.filter(provider=self.request.user)

    def destroy(self, request, *args, **kwargs):
        availability = self.get_object()
        if availability.bookings.filter(status__in=ACTIVE_STATUSES).exists():
            return _error("Ce créneau est réservé : annulez d'abord la réservation.")
        return super().destroy(request, *args, **kwargs)


class ProviderAvailabilityListView(generics.ListAPIView):
    """Créneaux libres et futurs d'un prestataire."""

    serializer_class = AvailabilitySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            Availability.objects
            .filter(
                provider_id=self.kwargs["provider_id"],
                is_active=True,
                date__gte=timezone.localdate(),
            )
            .exclude(bookings__status__in=ACTIVE_STATUSES)
            .select_related("provider")
        )


class CreateBookingView(APIView):

    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, availability_id):
        availability = get_object_or_404(
            Availability.objects.select_for_update(),
            pk=availability_id,
            is_active=True,
        )
        provider = availability.provider

        if provider == request.user:
            return _error("Vous ne pouvez pas réserver votre propre créneau.")

        if not is_provider(provider):
            return _error("Ce professionnel n'accepte pas de réservations.")

        profile = Profile.objects.filter(user=provider).first()
        if profile is None or not profile.is_available:
            return _error("Ce professionnel n'est pas disponible actuellement.")

        if profile.session_price is None:
            return _error("Ce professionnel n'a pas encore défini son tarif.")

        if _slot_start(availability) <= timezone.now():
            return _error("Ce créneau est déjà passé.")

        if Booking.objects.filter(
            availability=availability,
            status__in=ACTIVE_STATUSES,
        ).exists():
            return _error("Ce créneau est déjà réservé.", status.HTTP_409_CONFLICT)

        booking = Booking.objects.create(
            client=request.user,
            provider=provider,
            availability=availability,
            price=profile.session_price,
            message=request.data.get("message", ""),
        )

        create_notification(
            recipient=provider,
            sender=request.user,
            notification_type="booking_created",
            title="Nouvelle demande de réservation",
            message=f"{request.user.username} souhaite réserver un créneau.",
            resource_type="booking",
            resource_id=booking.id,
        )

        return Response(
            BookingSerializer(booking).data,
            status=status.HTTP_201_CREATED,
        )


class MyBookingsView(generics.ListAPIView):

    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            Booking.objects
            .filter(client=self.request.user)
            .select_related("client", "provider", "availability")
        )


class ReceivedBookingsView(generics.ListAPIView):

    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            Booking.objects
            .filter(provider=self.request.user)
            .select_related("client", "provider", "availability")
        )


class _ProviderActionView(APIView):
    """Base : action du prestataire sur une réservation reçue."""

    permission_classes = [IsAuthenticated]
    from_statuses = []
    to_status = ""
    notification_type = ""
    notification_title = ""
    require_started = False

    @transaction.atomic
    def post(self, request, pk):
        booking = get_object_or_404(
            Booking.objects.select_for_update().select_related("availability"),
            pk=pk,
            provider=request.user,
        )

        if booking.status not in self.from_statuses:
            return _error(
                f"Action impossible : la réservation est « {booking.status} »."
            )

        if self.require_started and _slot_start(booking.availability) > timezone.now():
            return _error("La session n'a pas encore commencé.")

        booking.status = self.to_status
        booking.save(update_fields=["status", "updated_at"])

        create_notification(
            recipient=booking.client,
            sender=request.user,
            notification_type=self.notification_type,
            title=self.notification_title,
            resource_type="booking",
            resource_id=booking.id,
        )

        return Response(BookingSerializer(booking).data)


class ConfirmBookingView(_ProviderActionView):
    from_statuses = ["PENDING"]
    to_status = "CONFIRMED"
    notification_type = "booking_confirmed"
    notification_title = "Votre réservation est confirmée"


class RejectBookingView(_ProviderActionView):
    from_statuses = ["PENDING"]
    to_status = "REJECTED"
    notification_type = "booking_rejected"
    notification_title = "Votre réservation a été refusée"


class CompleteBookingView(_ProviderActionView):
    """Marque la session comme terminée (ouvre le droit à l'avis)."""

    from_statuses = ["CONFIRMED"]
    to_status = "COMPLETED"
    notification_type = "booking_completed"
    notification_title = "Session terminée : laissez un avis"
    require_started = True


class CancelBookingView(APIView):
    """Annulation par le client ou le prestataire."""

    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, pk):
        booking = get_object_or_404(
            Booking.objects.select_for_update(),
            Q(client=request.user) | Q(provider=request.user),
            pk=pk,
        )

        if booking.status not in ["PENDING", "CONFIRMED"]:
            return _error(
                f"Impossible d'annuler une réservation « {booking.status} »."
            )

        booking.status = "CANCELLED"
        booking.save(update_fields=["status", "updated_at"])

        other = booking.provider if request.user == booking.client else booking.client
        create_notification(
            recipient=other,
            sender=request.user,
            notification_type="booking_cancelled",
            title="Réservation annulée",
            resource_type="booking",
            resource_id=booking.id,
        )

        return Response(BookingSerializer(booking).data)
