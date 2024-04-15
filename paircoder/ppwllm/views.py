from django.shortcuts import render
from jinja2 import (
    FileSystemLoader,
    select_autoescape,
    Environment
)
from pathlib import Path 
import logging
from dotenv import load_dotenv
from openai import OpenAI
import os


load_dotenv("D:\\gitFolders\\python_de_learners_data\\.env")
client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])

logging.basicConfig(format="%(message)s | %(levelname)s",
                    level=logging.INFO)

base_view = Path(__file__).parent
intent_clarifier = 'intent_clarifyer.prompt'

env = Environment(
    loader=FileSystemLoader(base_view / 'jinja_templates'),
    autoescape=select_autoescape,
)


def llm_call_openai(user_message:str):
    system_prompt = """You are an expert programmer, who is writing 
    code in all the programming languages available today, and solve 
    the challenge given. You reason step by step about the problem 
    and capabale of asking clarifying questions."""
    try:
        response = client.chat.completions.create(
            model='gpt-3.5-turbo',
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.0,
            top_p=1,
            frequency_penalty=0.1,
            presence_penalty=0.1
        )
        assistant_message = response.choices[0].message.content
        return {"response": assistant_message,
                'token_used': response.usage.totat_tokens}
    except Exception as e:
        logging.info(e)
        return {"error": "Error occurred while processing request."}


def index(request):
    return render(request, 'index.html', {"test": "delivered!!!"})


def intent(request):
    prompt = env.get_template(intent_clarifier)
    if request.POST:
        first_intent = request.POST.dict()
        input_prompt = prompt.render(**first_intent)
        llm_pred = llm_call_openai(user_message=input_prompt)
        first_intent['intent'] = llm_pred['response']
        output_prompt = prompt.render(**first_intent).strip()
        context = {"input_prompt": input_prompt,
                   "intent_pred": output_prompt,
                   "token_used": llm_pred['token_used']
                   }
    return render(request, 'index.html', context)


def pseudocode(request):
    pass