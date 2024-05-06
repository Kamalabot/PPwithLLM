from .consumer import ChatConsumer
from .code_consumer import CodeConsumer
from django.urls import re_path

websocket_urlpatterns = [
    re_path(r"ws/chat/(?P<chlng>\w+)/$", ChatConsumer.as_asgi()),
    re_path(r"ws/code/(?P<chlng>\w+)/$", CodeConsumer.as_asgi()),
]