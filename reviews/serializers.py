from rest_framework import serializers

from .models import Review


class ReviewSerializer(serializers.ModelSerializer):

    author_name = serializers.SerializerMethodField()
    professional_name = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = [
            "id",
            "booking",
            "author",
            "author_name",
            "professional",
            "professional_name",
            "rating",
            "comment",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "author",
            "professional",
            "created_at",
            "updated_at",
        ]

    def get_author_name(self, obj):
        return obj.author.get_full_name() or obj.author.username

    def get_professional_name(self, obj):
        return obj.professional.get_full_name() or obj.professional.username

    def validate_booking(self, booking):
        # En modification, la réservation ne change jamais.
        if self.instance is not None:
            return self.instance.booking

        request = self.context.get("request")
        if not request:
            return booking

        if booking.client != request.user:
            raise serializers.ValidationError(
                "Vous ne pouvez évaluer que vos propres réservations."
            )

        if booking.status != "COMPLETED":
            raise serializers.ValidationError(
                "Vous pourrez évaluer ce professionnel "
                "uniquement après une session terminée."
            )

        if Review.objects.filter(booking=booking).exists():
            raise serializers.ValidationError(
                "Cette réservation a déjà été évaluée."
            )

        return booking

    def create(self, validated_data):
        request = self.context["request"]
        booking = validated_data["booking"]

        return Review.objects.create(
            author=request.user,
            professional=booking.provider,
            **validated_data
        )

    def update(self, instance, validated_data):
        validated_data.pop("booking", None)
        return super().update(instance, validated_data)
