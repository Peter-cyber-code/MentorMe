from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError

from rest_framework import generics
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
)
from rest_framework.throttling import ScopedRateThrottle
from rest_framework_simplejwt.views import (
    TokenBlacklistView,
    TokenObtainPairView,
    TokenRefreshView,
)

from . import password_reset as pr
from .serializers import (
    RegisterSerializer,
    UserSerializer,
)


User = get_user_model()


class RegisterView(generics.CreateAPIView):

    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"


class ThrottledTokenObtainPairView(TokenObtainPairView):
    """Connexion, limitée en débit (anti brute-force)."""

    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"


class ThrottledTokenRefreshView(TokenRefreshView):

    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"


class LogoutView(TokenBlacklistView):
    """Révoque le refresh token (body : {"refresh": "..."})."""

    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"


class MeView(generics.RetrieveUpdateAPIView):

    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user



class PasswordForgotView(APIView):
    """Envoie un code par e-mail. Répond toujours pareil : on ne révèle pas si le compte existe."""

    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "password_reset"

    def post(self, request):
        user = pr.find_user(request.data.get("email"))
        if user:
            code = pr.issue_code(user)
            try:
                pr.send_code_email(user, code)
            except Exception:
                import logging
                logging.getLogger(__name__).exception("Envoi du code impossible")
        return Response(
            {"detail": "Si un compte existe pour cette adresse, un code vient d'être envoyé."}
        )


class PasswordResetView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"

    def post(self, request):
        invalid = Response(
            {"detail": "Code invalide ou expiré."},
            status=status.HTTP_400_BAD_REQUEST,
        )
        user = pr.find_user(request.data.get("email"))
        code = str(request.data.get("code", "")).strip()
        new_password = request.data.get("new_password") or ""

        if not user or not code:
            return invalid

        entry = pr.check_code(user, code)
        if entry is None:
            return invalid

        try:
            validate_password(new_password, user=user)
        except DjangoValidationError as exc:
            # le code n'est pas consommé : l'utilisateur peut corriger son mot de passe
            return Response(
                {"new_password": list(exc.messages)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(new_password)
        user.save(update_fields=["password"])
        entry.used = True
        entry.save(update_fields=["used"])
        pr.revoke_sessions(user)

        return Response({"detail": "Mot de passe modifié. Vous pouvez vous connecter."})



class SupportRequestView(APIView):
    """Formulaire « Nous contacter » : e-mail + description du problème (sans connexion)."""

    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "support"

    def post(self, request):
        from django.core.exceptions import ValidationError as DjValidationError
        from django.core.validators import validate_email

        from .models import SupportRequest

        email = (request.data.get("email") or "").strip()
        message = (request.data.get("message") or "").strip()

        try:
            validate_email(email)
        except DjValidationError:
            return Response(
                {"email": ["Saisissez une adresse e-mail valide."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if len(message) < 10:
            return Response(
                {"message": ["Décrivez votre problème en quelques mots (10 caractères minimum)."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        SupportRequest.objects.create(
            email=email,
            message=message[:2000],
            user=pr.find_user(email),
        )
        return Response(
            {"detail": "Message reçu. Notre équipe vous répond par e-mail dès que possible."},
            status=status.HTTP_201_CREATED,
        )
