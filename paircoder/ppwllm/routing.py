from .consumer import ChatConsumer
from django.urls import re_path

websocket_urlpatterns = [
    re_path(r"ws/chat/(?P<chlng>\w+)/$", ChatConsumer.as_asgi()),
]