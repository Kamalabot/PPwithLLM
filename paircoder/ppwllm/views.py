from django.shortcuts import (
    render,
    get_object_or_404,
    get_list_or_404,
    HttpResponse,
    redirect
    )
from django.db.utils import OperationalError
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
from .models import (
    Objective,
    Promptintent,
    Codesnippet
)
from .forms import ObjectiveForm
from typing import List
from groq import Groq
import re
import json


load_dotenv("D:\\gitFolders\\python_de_learners_data\\.env")
# load_dotenv("/mnt/d/gitFolders/python_de_learners_data/.env")
client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])
groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

logging.basicConfig(format="%(message)s | %(levelname)s",
                    level=logging.INFO)

base_view = Path(__file__).parent
intent_clarifier = 'intent_clarifyer.prompt'

env = Environment(
    loader=FileSystemLoader(base_view / 'jinja_templates'),
    autoescape=select_autoescape,
)


def extract_json(text):
    # Define the regular expression pattern
    pattern = r"```(.*?)```"

    # Use re.findall() to extract text between ```
    try:
        extracted_text = re.findall(pattern,
                                    text,
                                    re.DOTALL)
        # logging.info(extracted_text[0])
    # Print the extracted text
        # loaded_dict = json.loads(extracted_text[0])
        return extracted_text[0] 
    except Exception as e:
        logging.info(e)
        loaded_dict ={"error": "Unable to extract json"}
        return loaded_dict


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


def llm_groq_parser(user_message: str):
    user_prompt = f"""Review the message below and extract the data inside
    into JSON format and return the same. If the data contains multiple json
    data, then enclose into a list. Message: {user_message}"""
    data_engineer_prompt = f"""You are a data engineer, proficient in the use of 
    Large Language Models, and are tasked with identification of individual
    text messages and structuring each individual message in JSON format
    to create a knowledge graph from any given data.
    Unstructured Data: {user_message}"""
    try:
        response = groq_client.chat.completions.create(
            model='llama3-70b-8192',
            messages=[
                {
                    "role": "user",
                    # "content": user_prompt
                    "content": data_engineer_prompt,
                }
            ],
        )
        assistant_message = response.choices[0].message.content
        # parsed_text = extract_json(assistant_message)
        return assistant_message 
    except Exception as e:
        logging.info(e)
        return {"error": "Error occurred while processing request."}


def llm_text_parser(user_message: str):
    system_prompt = """You are an expert at parsing text of any type
    including variety of messages in whatsapp and other social media. You 
    extract the data present in the messages into a repeatable schema and 
    generate json format data."""
    user_prompt = f"""Review the message below and extract the data inside
    into JSON format and return the same. If the data contains multiple json
    data, then enclose into a list. Message: {user_message}"""
    try:
        response = client.chat.completions.create(
            model='gpt-3.5-turbo',
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.0,
            top_p=1,
            frequency_penalty=0.1,
            presence_penalty=0.1
        )
        assistant_message = response.choices[0].message.content
        parsed_text = extract_json(assistant_message)
        return parsed_text

    except Exception as e:
        logging.info(e)
        return {"error": "Error occurred while processing request."}


def post_message(request):
    return render(request, 'parse_message.html', {'message':'none'})


@csrf_exempt
def parse_message(request):
    if request.POST:
        dictionary = request.POST.dict()
        logging.debug(dictionary)
        message = str(dictionary['message'])
        parsed_openai = llm_text_parser(message)
        logging.info(f"openai: {parsed_openai}")
        parsed_llama3 = llm_groq_parser(message)
        logging.info(f"llama3: {parsed_llama3}")
        context = {
            "llama3_reply": parsed_llama3,
            "openai_reply": parsed_openai,
            "message": message
        }
        return render(request, 'parse_message.html', context)
    else:
        return render(reverse('page404'))


def challenge_index(request):
    try:
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
    except OperationalError:
        return render(request, 'chlnge_index.html', {"no_table": 'no_table'})


# starts with new_challenge of empty page
# page is filled with save challenge
# the load_challenge will call for loading challenge, and ready for checking intent
# then intent view will populate the front end.

def new_challenge(request):
    context = {"newchallenge": "placeholder",
               "input_prompt": "Prompt will be shown here",
               "chlng_id": "chat_0"} # this is just a placeholder
    return render(request, 'intent_page.html', context)


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


def delete_challenge(request, chlng_id):
    try:
        del_obj = get_object_or_404(Objective, pk=chlng_id)
        del_obj.delete()
        return redirect(reverse('home'))
    except Exception as e:
        logging.info(e)
        return redirect(reverse('page404'))


def delete_intent(request, itt_id):
    try:
        del_obj = get_object_or_404(Promptintent, pk=itt_id)
        del_obj.delete()
        return redirect(reverse('home'))
    except Exception as e:
        logging.info(e)
        return redirect(reverse('page404'))


def delete_snippet(request, sn_id):
    try:
        del_obj = get_object_or_404(Codesnippet, pk=sn_id)
        del_obj.delete()
        return redirect(reverse('home'))
    except Exception as e:
        logging.info(e)
        return redirect(reverse('page404'))

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
        conversation = "AI: " + intent_objs[0].user_intent + "\n"
        # this is the first intent
    else:
        return conversation
    for intent in intent_objs[1:]:
        conversation += "User: " + intent.user_feedback + '\n'
        if intent.llm_question != "No question from AI":
            conversation += "AI Question: " + intent.llm_question + '\n'
        else:
            conversation += "AI: " + intent.user_intent + '\n'
    return conversation


def load_challenge(request, chlng_id):
    chlng_obj = get_object_or_404(Objective, pk=chlng_id)
    int_objs = Promptintent.objects.all().filter(objective__pk=chlng_id)
    logging.info(int_objs)
    p_ints_len = len(int_objs)
    logging.info(p_ints_len)
    if p_ints_len > 0:
        final_prompt = int_objs[p_ints_len-1].input_prompt
        logging.info(f"final_prompt: {final_prompt}")
    else:
        final_prompt = "Prompt will be displayed here"
    int_data = []  # this is redundant
    for intent in int_objs:
        int_data.append(
            {
                "user_intent": intent.user_intent,
                "user_question": intent.user_question,
                "user_feedback": intent.user_feedback,
                "user_satisfied": intent.user_satisfied,
                "input_prompt": intent.input_prompt,
                "llm_question": intent.llm_question,
             }
        )
    assembled_dialogue = assemble_convo(int_objs)
    logging.info(assembled_dialogue)

    context = {"challenge": chlng_obj,
               "chlng_id": chlng_id,
               "intents": int_data,
               "assembled_dialogue": assembled_dialogue,
               "final_prompt": final_prompt}
   
    return render(request, 'intent_page.html', context)


def intent_question_extractor(llm_prediction: str):
    pred_lines = llm_prediction.split('\n')
    for idx, line in enumerate(pred_lines):
        logging.debug("Printing predicted results below as lines: \n")
        line = line.lower()
        logging.debug(f"Line-{idx}: {line}")
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


def code_extractor(llm_prediction: str):
    pattern1 = r"can_do:\s*(.*?)\s*Language:"
    pattern2 = r"Language:\s*(.*?)\s*```" 
    pattern3 = r"```(.*?)```"
    match1 = re.search(pattern1, llm_prediction)
    if match1:
        can_do = match1.group(1).strip()
    else:
        can_do = 'Not found'
    match2 = re.search(pattern2, llm_prediction)
    if match2:
        language = match2.group(1).strip()
    else:
        language = 'Not Found'
    match3 = re.search(pattern3, llm_prediction, re.DOTALL)
    if match3:
        snip = match3.group(1).strip()
    else:
        snip = 'Not Found'
    final_dict = dict(
        can_do=can_do,
        language=language,
        snip=snip
    )
    return final_dict


def intent_code_assembler(codesnips: Codesnippet):
    assembler = ""
    logging.info(len(codesnips))
    for ind, code in enumerate(codesnips):
        assembler += f"Intent: {code.intent.user_intent}"
        assembler += "\n\n"
        assembler += f"Snippet: {code_extractor(code.snippet)['snip']}"
        assembler += f"\n\n****** Conv {ind + 1} End********\n\n"

    return assembler 

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
                                 input_prompt=input_prompt,
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


def begin_coding(request, chlng_id):
    # get the final intent that is present in the Promptintent table
    related_intobj = Promptintent.objects.all().filter(objective__pk=chlng_id)
    intent_list = [obj.__dict__ for obj in related_intobj]
    # extract the other details from the objective table
    curr_obj = get_object_or_404(Objective, pk=chlng_id).__dict__
    # If code snippet is present for this chlnge, then update the same in code_page.html
    curr_obj_codes = Codesnippet.objects.all().filter(objective__id=chlng_id)

    if len(curr_obj_codes) > 0:
        curr_code_list = []
        for code_obj in curr_obj_codes:
            curr_code_list.append({
                "intent": code_obj.intent.id,
                "code_intent": code_obj.code_intent,
                "snippet": code_extractor(code_obj.snippet),
            })
        int_code_convo = intent_code_assembler(curr_obj_codes)
    else:
        curr_code_list = None
        intent_code_convo = ''

    context = {"intentdtl": intent_list,
               "currobj": curr_obj,
               "chlng_id": chlng_id,
               "curr_code_list": curr_code_list,
               "int_code_convo": int_code_convo} 

    logging.debug(f"context: {context}")
    return render(request, 'code_page.html', context)


def generate_code(request, itt_id):
    # get the prompt for code generation
    gen_code_prompt = env.get_template("code_generator.prompt")
    int_obj = get_object_or_404(Promptintent, pk=itt_id) 
    chlng_obj = get_object_or_404(Objective, pk=int_obj.objective_id) 
    intent_dtl = int_obj.user_intent
    chlng_dict = chlng_obj.__dict__

    code_prompt = gen_code_prompt.render(
        language=chlng_dict['language'],
        apptype=chlng_dict['apptype'],
        experience=chlng_dict['experience'],
        intent=intent_dtl,
    )
    logging.info(f'Code prompt: {code_prompt}')

    snippet = llm_call_openai(user_message=code_prompt)['response']

    cd_snippet = Codesnippet(
        objective=chlng_obj,
        intent=int_obj,
        code_intent=intent_dtl,
        snippet=snippet,
    )

    try:
        cd_snippet.save()
    except Exception as e:
        logging.info(f"There is issue in saving code snippet: {e}")
        return redirect(reverse('page404'))
    curr_obj_codes = Codesnippet.objects.all()
    int_code_convo = intent_code_assembler(curr_obj_codes)
    context = {
        "code_prompt": code_prompt,
        "snippet": code_extractor(snippet),
        "int_obj": int_obj,
        "int_code_convo": int_code_convo
    }
    return render(request, 'code_page.html', context)


def page404(request):
    return render(request, 'page404.html', {"error": "error"})


def viewtest(request):
    objt_form = ObjectiveForm()
    return render(request, 'index_test.html', {'form': objt_form})