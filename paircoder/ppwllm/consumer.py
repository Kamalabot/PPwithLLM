# the above scope has more info about the incoming websocket
# {'type': 'websocket', 'path': '/ws/chat/lobby/', 'raw_path': b'/ws/chat/lobby/', 
# 'root_path': '', 'headers': [(b'host', b'127.0.0.1:8000'), (b'upgrade',
# b'websocket'), (b'connection', b'Upgrade'), (b'sec-websocket-key', b'8Vtar+9LDUa49j5a5t3JnA=='),
# (b'sec-websocket-version', b'13'), (b'sec-websocket-extensions', 
# b'permessage-deflate; client_max_window_bits'), (b'user-agent', b'Python/3.11 websockets/12.0')],
# 'query_string': b'', 'client': ['127.0.0.1', 57688], 'server': ['127.0.0.1', 8000], 'subprotocols': [],
# 'asgi': {'version': '3.0'}, 'cookies': {}, 'session': <django.utils.functional.LazyObject object at 0x0000026D36BF2A50>,
# 'user': <channels.auth.UserLazyObject object at 0x0000026D36BF8710>, 'path_remaining': '',
# 'url_route': {'args': (), 'kwargs': {'chlng': 'lobby'}}}
import json
from channels.generic.websocket import (
    AsyncWebsocketConsumer
)
from channels.db import database_sync_to_async
from .models import Objective, Promptintent
from .views import (
    llm_call_openai,
    env,
)


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']["chlng"]
        # print(self.scope)
        self.room_group_name = f"chat_{self.room_name}"
        print(self.room_group_name)
        # the below adds the incoming consumer to the group
        await self.channel_layer.group_add(
            self.room_group_name, self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        # removes the incoming consumer from the group
        await self.channel_layer.group_discard(
            self.room_group_name, self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        # converts recd text data to dict
        print(text_data_json)
        if text_data_json:
            prompt_temp = env.get_template("intent_modifier.prompt")
            prompt_text = prompt_temp.render(**text_data_json)
            llm_pred = llm_call_openai(user_message=prompt_text)
            print(llm_pred)
            await self.send(text_data=json.dumps(llm_pred))

        # the following seems to be broadcasting the message to all
        # await self.channel_layer.group_send(
            # self.room_group_name, {"type": "chat_message", "message": message}
        # )

    # recv message from room grp
    async def chat_message(self, event):
        message = event['message']
        if message == 'challenges':
            challenges = await self.get_challenges()
            chlng_json = {"rows": challenges}
            await self.send(text_data=json.dumps(chlng_json))


    @database_sync_to_async
    def get_challenges(self):
        table_objs = Objective.objects.all() 
        table_data = []
        for obj in table_objs:
            table_data.append({
                "challenge": obj.challenge,
                "language": obj.language,
                "apptype": obj.apptype,
                "experience": obj.experience
            })
        return table_data