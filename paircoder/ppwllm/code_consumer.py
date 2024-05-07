import json
from channels.generic.websocket import (
    AsyncWebsocketConsumer
)
from channels.db import database_sync_to_async
from .models import Objective, Promptintent, Codesnippet
from .views import (
    llm_call_openai,
    env,
    code_extractor,
    intent_code_assembler,
    start_codechat
)
import logging

logging.basicConfig(format="%(message)s | %(levelname)s",
                    level=logging.INFO)


class CodeConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['chlng']
        self.room_group_name = f"code_{self.room_name}"
        await self.channel_layer.group_add(
            self.room_group_name, self.channel_name
        )
        # logging.info(self.room_group_name)
        # logging.info(self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name, self.channel_name
        )

    async def receive(self, text_data):
        logging.info("recieving")
        logging.info(text_data)
        code_dict = json.loads(text_data)
        itt_id = code_dict['itt_id']
        user_msg = code_dict['user_msg']
        codeconv = code_dict['codeconv']
        codesnips = await self.get_codesnippets(itt_id)
        # recieved user message is parsed for the intent
        # based on the intent code is altered 
        # altered code is updated in db
        # and sent to the frontend
        json_str = json.dumps({"reply": "ack"})
        await self.send(text_data=json_str)

    async def chat_message(self, event):
        message = event['message']
        logging.info(message)
        await self.send(json.dumps({"message": message}))

    @database_sync_to_async
    def get_codesnippets(self, itt_id):
        snip_queryset = Codesnippet.objects.all().filter(intent__pk=itt_id)
        logging.info(snip_queryset)