# from django.urls import re_path

# # from . import consumers

# # websocket_urlpatterns = [
# #     re_path(r'ws/booking/(?P<shop_id>[-\w]+)/$', consumers.BookingConsumer.as_asgi()),
# # ]
 

# # your_app/routing.py
# from django.urls import path
# from .consumers import ChatConsumer, NotificationConsumer

# websocket_urlpatterns = [
#     re_path(r"ws/chat/(?P<conversation_id>\w+)/$", ChatConsumer.as_asgi()),
#     path("ws/notifications/", NotificationConsumer.as_asgi()),
# ]


from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    re_path(r"ws/chat/(?P<chat_id>[^/]+)/$", consumers.ChatConsumer.as_asgi()),
    re_path(r"ws/startChat/(?P<store_or_user_id>[^/]+)/$", consumers.StartCoversationConsumer.as_asgi()
    ),    # path("ws/notifications/", consumers.NotificationConsumer.as_asgi()),
]
 
