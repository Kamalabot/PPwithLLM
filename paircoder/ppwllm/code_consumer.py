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


def code_alterer(jinja_env, user_feedback, snippet):
    prompt_temp = jinja_env.get_template('code_modifier.prompt')
    prompt = prompt_temp.render(user_feedback=user_feedback,
                                code=snippet)
    llm_pred = llm_call_openai(user_message=prompt)       
    return llm_pred['response']


class CodeConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['chlng']
        self.room_group_name = f"code_{self.room_name}"
        # await self.channel_layer.group_add(
            # self.room_group_name, self.channel_name
        # )
        # logging.info(self.room_group_name)
        # logging.info(self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        pass
        # await self.channel_layer.group_discard(
            # self.room_group_name, self.channel_name
        # )

    async def receive(self, text_data):
        logging.info("recieving")
        logging.info(text_data)
        code_dict = json.loads(text_data)
        itt_id = code_dict['itt_id']
        codeconv = code_dict['codeconv']
        codesnips = await self.get_codesnippets(itt_id)
        # recieved user message from the ws client
        user_msg = code_dict['user_msg']
        # based on the user message and previous discussion code is altered
        code_update = code_alterer(env, user_msg, codeconv)
        # altered code is updated in db
        logging.info(code_update)
        # build the row for code_snippets table
        snippet_dict = dict(
            objective=codesnips[0]['objective'],
            intent=codesnips[0]['intent'],
            user_input=user_msg,
            snippet=code_update,
        )
        row_id = await self.write_codesnippets(snippet_dict)
        # and sent to the frontend
        json_str = json.dumps({"user_msg": user_msg,
                               "updated_code": code_update})
        await self.send(text_data=json_str)

    async def chat_message(self, event):
        message = event['message']
        logging.info(message)
        await self.send(json.dumps({"message": message}))

    @database_sync_to_async
    def get_codesnippets(self, itt_id):
        snip_queryset = Codesnippet.objects.all().filter(intent__pk=itt_id)
        snip_array = []
        for snip in snip_queryset:
            snip_array.append({
                "objective": snip.objective,
                "intent": snip.intent,
                "code_intent": snip.code_intent,
                "user_input": snip.user_input,
                "snippet": snip.snippet,
            })
        return snip_array

    @database_sync_to_async
    def write_codesnippets(self, snipdict):
        snipobj = Codesnippet(**snipdict)
        snipobj.save()
        return snipobj.pk
