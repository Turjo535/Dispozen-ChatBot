# """
# ASGI config for DispozenProject project.

# It exposes the ASGI callable as a module-level variable named ``application``.

# For more information on this file, see
# https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
# """

# # yourproject/asgi.py

# import os
# from django.core.asgi import get_asgi_application
# from channels.routing import ProtocolTypeRouter, URLRouter
# from channels.auth import AuthMiddlewareStack
# from django.urls import path
# from DispozenApp import consumers  # Import your consumers
# from DispozenApp import routing  # Import routing configuration

# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'DispozenProject.settings')

# application = ProtocolTypeRouter({
#     "http": get_asgi_application(),
#     "websocket": AuthMiddlewareStack(  # WebSocket handling
#             # Define WebSocket routes for consumers
#             # path("ws/notifications/", consumers.NotificationConsumer.as_asgi()),
#             routing.websocket_urlpatterns
#             DispozenApp.routing.websocket_urlpatterns
#         )
#     ),
# })


import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from DispozenApp.middleware import JWTAuthMiddleware
import DispozenApp.routing  

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'DispozenProject.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": JWTAuthMiddleware(
        URLRouter(
            DispozenApp.routing.websocket_urlpatterns
        )
    ),
})


