# import os
# import django
# from django.core.asgi import get_asgi_application

# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'marketplace.settings')

# # Add this to ensure apps are loaded before importing anything else
# django.setup()

# application = get_asgi_application()

# # Import WebSocket routing only after setup
# from chat.routing import websocket_urlpatterns  # noqa isort:skip
# from channels.routing import ProtocolTypeRouter, URLRouter
# from channels.auth import AuthMiddlewareStack

# application = ProtocolTypeRouter({
#     "http": get_asgi_application(),
#     "websocket": AuthMiddlewareStack(URLRouter(websocket_urlpatterns)),
# })


"""
ASGI config for marketplace project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os
import django


from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'marketplace.settings')

# Add this to ensure apps are loaded before importing anything else
django.setup()

from chat.middleware import JWTAuthMiddleware  # Import your middleware
import chat.routing

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        JWTAuthMiddleware(
            URLRouter(
                chat.routing.websocket_urlpatterns  # Correct the typo here
            )
        )
    ),
})


