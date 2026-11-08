"""Authentification JWT pour les WebSockets (Django Channels).

Le client Flutter se connecte avec :
    ws://hote/ws/messaging/<conversation_id>/?token=<access_token>

Le token d'accès est de courte durée (15 min) ; le client doit se reconnecter
avec un token frais après un refresh.
"""
from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken


@database_sync_to_async
def _get_user(token_str):
    try:
        token = AccessToken(token_str)
        user = get_user_model().objects.get(pk=token["user_id"])
    except (TokenError, KeyError, get_user_model().DoesNotExist):
        return AnonymousUser()
    return user if user.is_active else AnonymousUser()


class JWTAuthMiddleware(BaseMiddleware):

    async def __call__(self, scope, receive, send):
        query = parse_qs(scope.get("query_string", b"").decode())
        token = (query.get("token") or [None])[0]
        scope["user"] = await _get_user(token) if token else AnonymousUser()
        return await super().__call__(scope, receive, send)
