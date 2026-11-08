from django.urls import path

from .views import (
    SupportRequestView,
    PasswordForgotView,
    PasswordResetView,
    LogoutView,
    MeView,
    RegisterView,
    ThrottledTokenObtainPairView,
    ThrottledTokenRefreshView,
)


urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", ThrottledTokenObtainPairView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("token/refresh/", ThrottledTokenRefreshView.as_view(), name="token-refresh"),
    path("password/forgot/", PasswordForgotView.as_view(), name="password-forgot"),
    path("password/reset/", PasswordResetView.as_view(), name="password-reset"),
    path("support/", SupportRequestView.as_view(), name="support"),
    path("me/", MeView.as_view(), name="me"),
]
