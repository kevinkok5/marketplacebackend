import jwt
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import get_user_model
from urllib.parse import parse_qs
from channels.middleware import BaseMiddleware  # ✅ Correct
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from channels.db import database_sync_to_async

User = get_user_model()

class JWTAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        subprotocols = scope.get("subprotocols", [])
        token = subprotocols[1] if len(subprotocols) > 0 else None

        # Look for the token in the query string or headers
        if token:
            try:
                UntypedToken(token)  # Validate token format
                auth = JWTAuthentication()
                validated_token = auth.get_validated_token(token)
                user = await database_sync_to_async(auth.get_user)(validated_token)
                scope["user"] = user  # Assign authenticated user
            except (InvalidToken, jwt.ExpiredSignatureError, jwt.DecodeError):
                scope["user"] = AnonymousUser()
        else:
            scope["user"] = AnonymousUser()

        return await super().__call__(scope, receive, send)
    
# class JWTAuthMiddleware(BaseMiddleware):
#     async def __call__(self, scope, receive, send):
#         query_string = parse_qs(scope["query_string"].decode())

#         # Look for the token in the query string or headers
#         token = None
#         if "token" in query_string:
#             token = query_string["token"][0]
#         elif "authorization" in scope["headers"]:
#             auth_header = dict(scope["headers"]).get(b"authorization", b"").decode()
#             if auth_header.startswith("Bearer "):
#                 token = auth_header.split(" ")[1]

#         if token:
#             try:
#                 UntypedToken(token)  # Validate token format
#                 auth = JWTAuthentication()
#                 validated_token = auth.get_validated_token(token)
#                 user = await database_sync_to_async(auth.get_user)(validated_token)
#                 scope["user"] = user  # Assign authenticated user
#             except (InvalidToken, jwt.ExpiredSignatureError, jwt.DecodeError):
#                 scope["user"] = AnonymousUser()
#         else:
#             scope["user"] = AnonymousUser()

#         return await super().__call__(scope, receive, send)
