from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError

from rest_framework import serializers

from profiles.models import Role
from profiles.roles import SELF_ASSIGNABLE_ROLE_CODES, user_role_codes


User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):

    password = serializers.CharField(
        write_only=True,
        min_length=8
    )

    password_confirm = serializers.CharField(write_only=True)

    # Seuls les rôles « libres » sont acceptés à l'inscription.
    # Mentor / investisseur / experts passent par la vérification.
    role = serializers.ChoiceField(
        choices=sorted(SELF_ASSIGNABLE_ROLE_CODES),
        default="project_owner",
        write_only=True,
        required=False
    )

    class Meta:
        model = User

        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "password",
            "password_confirm",
            "role",
        ]

        read_only_fields = ["id"]

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError(
                "Cette adresse e-mail est déjà utilisée."
            )
        return value.lower()

    def validate(self, attrs):
        password = attrs.get("password")
        password_confirm = attrs.pop("password_confirm", None)

        if password != password_confirm:
            raise serializers.ValidationError(
                {"password_confirm": "Les mots de passe ne correspondent pas."}
            )

        candidate = User(
            username=attrs.get("username", ""),
            email=attrs.get("email", ""),
            first_name=attrs.get("first_name", ""),
            last_name=attrs.get("last_name", ""),
        )

        try:
            validate_password(password, user=candidate)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(
                {"password": list(exc.messages)}
            )

        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password")
        role_code = validated_data.pop("role", "project_owner")

        user = User.objects.create_user(
            password=password,
            **validated_data
        )

        # Le profil est créé par le signal post_save de profiles.
        role, _ = Role.objects.get_or_create(code=role_code)
        user.profile.roles.add(role)

        return user


class UserSerializer(serializers.ModelSerializer):

    full_name = serializers.SerializerMethodField()

    roles = serializers.SerializerMethodField()

    class Meta:
        model = User

        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "roles",
            "rating",
        ]

        read_only_fields = [
            "id",
            "username",
            "email",
            "full_name",
            "roles",
            "rating",
        ]

    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username

    def get_roles(self, obj):
        return sorted(user_role_codes(obj))
