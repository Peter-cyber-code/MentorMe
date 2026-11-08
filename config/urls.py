from django.conf import settings
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path, re_path
from django.views.static import serve

from accounts.views import (
    ThrottledTokenObtainPairView,
    ThrottledTokenRefreshView,
)


def health(request):
    """Sonde de disponibilité pour le déploiement (load balancer, k8s)."""
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", health, name="health"),

    # Alias historiques, désormais limités en débit
    path("api/token/", ThrottledTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", ThrottledTokenRefreshView.as_view(), name="token_refresh"),

    path("api/accounts/", include("accounts.urls")),
    path("api/projects/", include("projects.urls")),
    path("api/posts/", include("posts.urls")),
    path("api/messaging/", include("messaging.urls")),
    path("api/follows/", include("follows.urls")),
    path("api/profiles/", include("profiles.urls")),
    path("api/booking/", include("booking.urls")),
    path("api/matching/", include("matching.urls")),
    path("api/reviews/", include("reviews.urls")),
    path("api/notifications/", include("notifications.urls")),
    path("api/audits/", include("audit_ai.urls")),
    path("api/calls/", include("calls.urls")),
]

if settings.DEBUG or settings.SERVE_MEDIA:
    urlpatterns += [
        re_path(r"^media/(?P<path>.*)$", serve, {"document_root": settings.MEDIA_ROOT}),
    ]
