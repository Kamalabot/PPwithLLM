from django.shortcuts import render
from jinja2 import (
    FileSystemLoader,
    select_autoescape,
    Environment
)
from pathlib import Path 
import logging
import os


logging.basicConfig(format="%(message)s | %(levelname)s",
                    level=logging.INFO)

base_view = Path(__file__).parent
intent_clarifier = 'intent_clarifyer.prompt'

env = Environment(
    loader=FileSystemLoader(base_view / 'jinja_templates'),
    autoescape=select_autoescape,
)


def index(request):
    return render(request, 'index.html', {"test": "delivered!!!"})


def intent(request):
    prompt = env.get_template(intent_clarifier)
    if request.POST:
        first_intent = request.POST.dict()
        output_prompt = prompt.render(**first_intent)
    return render(request, 'index.html', {"int_prompt": output_prompt})


def pseudocode(request):
    pass