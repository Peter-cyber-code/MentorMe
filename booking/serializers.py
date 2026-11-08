from django.utils import timezone
from rest_framework import serializers

from .models import (
    Availability,
    Booking,
)


class AvailabilitySerializer(serializers.ModelSerializer):

    provider_name = serializers.CharField(
        source="provider.username",
        read_only=True
    )

    is_booked = serializers.SerializerMethodField()

    class Meta:
        model = Availability
        fields = [
            "id",
            "provider",
            "provider_name",
            "date",
            "start_time",
            "end_time",
            "is_active",
            "is_booked",
            "created_at",
        ]
        read_only_fields = [
            "provider",
            "created_at",
        ]

    def get_is_booked(self, obj):
        return obj.bookings.filter(
            status__in=["PENDING", "CONFIRMED", "COMPLETED"]
        ).exists()

    def validate(self, attrs):
        instance = self.instance

        start = attrs.get("start_time", getattr(instance, "start_time", None))
        end = attrs.get("end_time", getattr(instance, "end_time", None))
        date = attrs.get("date", getattr(instance, "date", None))

        if start and end and start >= end:
            raise serializers.ValidationError(
                "L'heure de fin doit être après l'heure de début."
            )

        if instance is None and date and date < timezone.localdate():
            raise serializers.ValidationError(
                {"date": "Impossible de créer une disponibilité dans le passé."}
            )

        request = self.context.get("request")
        if request and request.user.is_authenticated and date and start and end:
            overlapping = Availability.objects.filter(
                provider=request.user,
                date=date,
                is_active=True,
                start_time__lt=end,
                end_time__gt=start,
            )
            if instance is not None:
                overlapping = overlapping.exclude(pk=instance.pk)
            if overlapping.exists():
                raise serializers.ValidationError(
                    "Ce créneau chevauche une disponibilité existante."
                )

        return attrs


class BookingSerializer(serializers.ModelSerializer):

    client_name = serializers.CharField(
        source="client.username",
        read_only=True
    )

    provider_name = serializers.CharField(
        source="provider.username",
        read_only=True
    )

    availability_detail = AvailabilitySerializer(
        source="availability",
        read_only=True
    )

    class Meta:
        model = Booking
        fields = [
            "id",
            "client",
            "client_name",
            "provider",
            "provider_name",
            "availability",
            "availability_detail",
            "price",
            "status",
            "message",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "client",
            "provider",
            "price",
            "status",
            "created_at",
            "updated_at",
        ]
