from rest_framework import serializers

from .models import (
    RoleRequest,
    Profile,
    Role,
    Expertise,
)
from .roles import PRIVILEGED_ROLE_CODES


class RoleSerializer(serializers.ModelSerializer):

    label = serializers.CharField(
        source="get_code_display",
        read_only=True
    )

    class Meta:
        model = Role
        fields = ["id", "code", "label"]


class ExpertiseSerializer(serializers.ModelSerializer):

    class Meta:
        model = Expertise
        fields = ["id", "name"]


class ProfileSerializer(serializers.ModelSerializer):

    user_id = serializers.IntegerField(
        source="user.id",
        read_only=True
    )

    username = serializers.CharField(
        source="user.username",
        read_only=True
    )

    full_name = serializers.SerializerMethodField()

    completion = serializers.SerializerMethodField()

    rating = serializers.FloatField(
        source="user.rating",
        read_only=True
    )

    roles = RoleSerializer(many=True, read_only=True)

    expertise = ExpertiseSerializer(many=True, read_only=True)

    role_ids = serializers.PrimaryKeyRelatedField(
        queryset=Role.objects.all(),
        source="roles",
        many=True,
        write_only=True,
        required=False
    )

    expertise_ids = serializers.PrimaryKeyRelatedField(
        queryset=Expertise.objects.all(),
        source="expertise",
        many=True,
        write_only=True,
        required=False
    )

    class Meta:
        model = Profile

        fields = [
            "id",
            "user_id",
            "username",
            "full_name",
            "photo",
            "headline",
            "bio",
            "country",
            "city",
            "roles",
            "role_ids",
            "expertise",
            "expertise_ids",
            "session_price",
            "session_duration",
            "is_available",
            "is_verified",
            "rating",
            "completion",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "user_id",
            "username",
            "full_name",
            "is_verified",
            "created_at",
            "updated_at",
        ]

    def get_completion(self, obj):
        checks = [
            bool(obj.photo),
            bool(obj.headline.strip()),
            bool(obj.bio.strip()),
            bool(obj.city.strip()),
            bool(obj.country.strip()),
            obj.expertise.exists(),
        ]
        return round(sum(checks) / len(checks) * 100)

    def get_full_name(self, obj):
        return obj.user.get_full_name() or obj.user.username

    def validate_role_ids(self, roles):
        """
        Les rôles sensibles (mentor, investisseur, experts) ne peuvent pas
        être pris librement : il faut un profil vérifié, ou que le rôle ait
        déjà été attribué (par un administrateur).
        """
        requested = {role.code for role in roles}
        privileged = requested & PRIVILEGED_ROLE_CODES

        if not privileged:
            return roles

        profile = self.instance
        already_held = set()
        verified = False

        if profile is not None:
            verified = profile.is_verified
            already_held = set(
                profile.roles.values_list("code", flat=True)
            )

        newly_requested = privileged - already_held

        if newly_requested and not verified:
            raise serializers.ValidationError(
                "Ces rôles nécessitent une vérification de votre profil : "
                + ", ".join(sorted(newly_requested))
            )

        return roles

    def validate_session_price(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError(
                "Le tarif ne peut pas être négatif."
            )
        return value

    def validate_session_duration(self, value):
        if value is not None and value <= 0:
            raise serializers.ValidationError(
                "La durée doit être positive."
            )
        return value



class RoleRequestSerializer(serializers.ModelSerializer):

    role = serializers.SlugRelatedField(
        slug_field="code",
        queryset=Role.objects.all()
    )

    role_label = serializers.SerializerMethodField()

    class Meta:
        model = RoleRequest
        fields = [
            "id",
            "role",
            "role_label",
            "message",
            "status",
            "admin_note",
            "created_at",
            "reviewed_at",
        ]
        read_only_fields = [
            "status",
            "admin_note",
            "created_at",
            "reviewed_at",
        ]

    def get_role_label(self, obj):
        return obj.role.get_code_display()

    def validate_role(self, role):
        user = self.context["request"].user

        if role.code not in PRIVILEGED_ROLE_CODES:
            raise serializers.ValidationError(
                "Ce rôle ne nécessite pas de validation."
            )

        if user.profile.roles.filter(pk=role.pk).exists():
            raise serializers.ValidationError(
                "Vous avez déjà ce rôle."
            )

        if RoleRequest.objects.filter(
            user=user, role=role, status="pending"
        ).exists():
            raise serializers.ValidationError(
                "Une demande est déjà en cours pour ce rôle."
            )

        return role

    def validate_message(self, value):
        if len(value.strip()) < 20:
            raise serializers.ValidationError(
                "Présentez-vous en quelques phrases (20 caractères minimum)."
            )
        return value.strip()

    def create(self, validated_data):
        return RoleRequest.objects.create(
            user=self.context["request"].user,
            **validated_data
        )
