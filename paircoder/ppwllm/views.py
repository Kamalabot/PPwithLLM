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
from typing import List


load_dotenv("D:\\gitFolders\\python_de_learners_data\\.env")
# load_dotenv("/mnt/d/gitFolders/python_de_learners_data/.env")
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


# starts with new_challenge of empty page
# page is filled with save challenge
# the load_challenge will call for loading challenge, and ready for checking intent
# then intent view will populate the front end.

def new_challenge(request):
    return render(request, 'intent_page.html', {"newchallenge": "New challenge"})


def save_challenge(request):
    if request.POST:
        first_intent = request.POST.dict()
        objective_obj = Objective(challenge=first_intent['challenge'],
                                  language=first_intent['language'],
                                  apptype=first_intent['apptype'],
                                  experience=first_intent['experience'])

        objective_obj.save()
        context = dict(**first_intent)
        return redirect(reverse('load_chlng', args=[objective_obj.pk]))

    return render(request, 'intent_page.html', context)


def dbobj_to_prompt(db_obj, jinja_env):
    prompt = jinja_env.get_template(intent_clarifier)
    chlng_dict = dict(challenge=db_obj.challenge,
                      apptype=db_obj.apptype,
                      language=db_obj.language,
                      experience=db_obj.experience)
    return prompt.render(**chlng_dict)


def assemble_convo(intent_objs: List[Promptintent]):
    conversation = ""
    if len(intent_objs) > 0:
        conversation = intent_objs[0].user_intent  # this is the first intent
    else:
        return conversation
    for intent in intent_objs[1:]:
        conversation += "AI: " + intent.user_intent + '\n'
        conversation += "User: " + intent.user_feedback + '\n'
    return conversation


def load_challenge(request, chlng_id):
    chlng_obj = get_object_or_404(Objective, pk=chlng_id)
    int_objs = Promptintent.objects.all().filter(objective__pk=chlng_id)
    int_data = []  # this is redundant
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
    assembled_dialogue = assemble_convo(int_objs)
    logging.info(assembled_dialogue)

    context = {"challenge": chlng_obj,
               "chlng_id": chlng_id,
               "intents": int_data,
               "assembled_dialogue": assembled_dialogue}
   
    return render(request, 'intent_page.html', context)


def intent_question_extractor(llm_prediction: str):
    pred_lines = llm_prediction.split('\n')
    for idx, line in enumerate(pred_lines):
        logging.info("Printing predicted results below as lines: \n")
        line = line.lower()
        logging.info(f"Line-{idx}: {line}")
        if 'intent:' in line:
            pred_intent = line.split('intent:')[1]
        if 'question:' in line:
            pred_question = line.split('question:')[1]
    try:
        pred_intent
    except NameError:
        pred_intent = 'Unable to locate intent, recheck prompt'
    try:
        pred_question
    except NameError:
        pred_question = 'No question from AI'

    return {"pred_intent": pred_intent,
            "pred_question": pred_question}


def intent(request, chlng_id):
    prompt = env.get_template(intent_clarifier)
    try:
        chlng_obj = get_object_or_404(Objective, pk=chlng_id)
        chlng_dict = dict(challenge=chlng_obj.challenge,
                          apptype=chlng_obj.apptype,
                          language=chlng_obj.language,
                          experience=chlng_obj.experience)
        input_prompt = prompt.render(**chlng_dict)
        llm_pred = llm_call_openai(user_message=input_prompt)

        user_feedback = 'Provide your feedback here...'
        processed_pred = intent_question_extractor(llm_pred['response'])
        logging.info(f"processed pred: {processed_pred}")
        promptint = Promptintent(objective=chlng_obj,
                                 user_intent=processed_pred['pred_intent'],
                                 user_question=chlng_obj.challenge,
                                 user_feedback=user_feedback,
                                 llm_question=processed_pred['pred_question'])
        promptint.save()

        context = {
            "challenge": chlng_dict,
            "chlng_id": chlng_id,
            "input_prompt": input_prompt,
            "intent_pred": processed_pred['pred_intent'],
            "user_feedback": user_feedback
        }
        return render(request, 'intent_page.html', context)
     
    except Exception as e:
        logging.info(e)
        return redirect('page404')


def page404(request):
    return render(request, 'page404.html', {"error": "error"})


def viewtest(request):
    objt_form = ObjectiveForm()
    return render(request, 'index_test.html', {'form': objt_form})