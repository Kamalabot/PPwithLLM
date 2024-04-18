from django.shortcuts import (
    render,
    get_object_or_404,
    get_list_or_404,
    HttpResponse,
    redirect
    )

from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
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
from .models import Objective, Promptintent
from .forms import ObjectiveForm


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


def llm_call_openai(user_message: str):
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
                'token_used': response.usage.total_tokens}
    except Exception as e:
        logging.info(e)
        return {"error": "Error occurred while processing request."}


def challenge_index(request):
    chlng_objs = Objective.objects.all().order_by('challenge')
    obj_data = []
    for chlng in chlng_objs:
        obj_data.append({
            "id": chlng.pk,
            "challenge": chlng.challenge,
            "language": chlng.language,
            "apptype": chlng.apptype,
            "experience": chlng.experience
        })
    logging.info(obj_data)
    return render(request, 'chlnge_index.html', {"challenges": obj_data})


def new_challenge(request):
    return render(request, 'intent_page.html', {"challenge": "New challenge"})


def save_challenge(request):
    if request.POST:
        first_intent = request.POST.dict()
        objective_obj = Objective(challenge=first_intent['challenge'],
                                  language=first_intent['language'],
                                  apptype=first_intent['apptype'],
                                  experience=first_intent['experience'])

        objective_obj.save()
        context = dict(**first_intent)

    return render(request, 'intent_page.html', context)


def load_challenge(request, chlng_id):
    chlng_obj = get_object_or_404(Objective, pk=chlng_id)
    int_objs = Promptintent.objects.all().filter(objective__pk=chlng_id)
    int_data = []
    for intent in int_objs:
        int_data.append(
            {
                "user_intent": intent.user_intent,
                "user_question": intent.user_question,
                "user_feedback": intent.user_feedback,
                "user_satisfied": intent.user_satisfied,
                "llm_question": intent.llm_question,
             }
        )
    context = {"challenge": chlng_obj,
               "intents": int_data}
    return render(request, 'challenge_page.html', context)


def intent(request):
    prompt = env.get_template(intent_clarifier)
    if request.POST:
        first_intent = request.POST.dict()
        logging.info(first_intent)
        input_prompt = prompt.render(**first_intent)
 
        objective_obj = Objective(challenge=first_intent['challenge'],
                                  language=first_intent['language'],
                                  apptype=first_intent['apptype'],
                                  experience=first_intent['experience'])

        objective_obj.save()

        llm_pred = llm_call_openai(user_message=input_prompt)
        first_intent['intent'] = llm_pred['response']
        user_feedback = 'Requesting Feedback'
        logging.info(llm_pred['response'])

        promptint = Promptintent(objective=objective_obj,
                                 user_intent=llm_pred["response"],
                                 user_question=first_intent['challenge'],
                                 user_feedback=user_feedback,
                                 llm_question='No Question')
        promptint.save()

        context = {
            "chlng_id": objective_obj.pk,
            "input_prompt": input_prompt,
            "intent_pred": llm_pred,
            "user_feedback": user_feedback
        }
        return render(request, 'intent_page.html', context)

    return redirect('page404')


def page404(request):
    return render(request, 'page404.html', {"error": "error"})


def viewtest(request):
    objt_form = ObjectiveForm()
    return render(request, 'index_test.html', {'form': objt_form})