import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

django_asgi_app = get_asgi_application()

from channels.routing import ProtocolTypeRouter, URLRouter  # noqa: E402

from config.jwt_ws import JWTAuthMiddleware  # noqa: E402
from messaging.routing import websocket_urlpatterns  # noqa: E402

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    # Pas d'AllowedHostsOriginValidator : les clients mobiles (Flutter/dart:io)
    # n'envoient pas d'en-tête Origin. L'authentification repose sur le JWT
    # (pas sur un cookie), donc le risque de détournement cross-site est nul.
    "websocket": JWTAuthMiddleware(URLRouter(websocket_urlpatterns)),
})
