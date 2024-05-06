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
    Codesnippet,
    Messagestore,
    Rawcontent
)
from .forms import ObjectiveForm
from typing import List
from groq import Groq
from re import (
    compile,
    search,
    DOTALL,
)
import json
from datetime import datetime


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


def format_dtime(date_str):
    datepart = date_str.split(' ')[0]
    print(datepart)
    if len(datepart) == 8:
        return datetime.strptime(date_str, '%d/%m/%y %H:%M')
    return datetime.strptime(date_str, '%d/%m/%Y %H:%M')


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
    data_engineer_prompt = """You are a data engineer, proficient in the use of 
    Large Language Models, and are tasked with identification of individual
    text messages and structuring each individual message in JSON format as 
    shown below ```json {
            "rental_details": {
                "description": "RENTAL ROOM HIGHER FLOOR SEAFACE",
                "room_type": "1RK",
                "carpet_area": "225 sq.ft",
                "allowed": ["BACHELOR", "FAMILY"],
                "rent_amount": 25000,
                "deposit_amount": 100000,
                "negotiable": false,
                "location": ["JUHU VERSOVA LINK ROAD", "ANDHERI WEST"]
            },
            "contact_numbers": ["7977346657", "9324104596"]}```
    Do not provide explanation of any kind.""" + f"""Unstructured Data: {user_message}"""

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
        return assistant_message 

    except Exception as e:
        logging.info(e)
        return {"error": "Error occurred while processing request."}


def post_message(request):
    try:
        raw_objs = Rawcontent.objects.all()
        raw_messages = []
        for raw in raw_objs:
            raw_messages.append(
                {
                    "content": raw.content,
                    "id": raw.pk
                }
            )
        return render(request, 'parse_message.html',
                      {'raw_objs': raw_messages})
    except Exception as e:
        logging.info(e)
        return redirect(reverse('page404'))


def msg_to_db(message, source):
    parts_regex = compile(r"(\d{2}\/\d{2}\/\d{4}),\s(\d{2}:\d{2})\s-\s(\+\d{2}\s\d{5}\s\d{5}):")  # extracting the date and time
    data_locs = parts_regex.finditer(message)
    # data_len = len(data_locs)
    split_regex = compile(r"\d{2}\/\d{2}\/\d{4},\s\d{2}:\d{2}\s-\s\+\d{2}\s\d{5}\s\d{5}:")  # extracting the date and time 
    message_content = split_regex.split(message)[1:]
    msg_len = len(message_content)
    if msg_len == 0:
        logging.info(f"Message_len: {msg_len}, so trying another regex")
        comp_en = compile(r"(\d{2}\/\d{2}\/\d{2}),\s(\d{2}:\d{2})\s.{2}\s-\s([a-zA-Z0-9_]*):")  # extracting the date and time
        data_locs = comp_en.finditer(message)

        comp_sp = compile(r"\d{2}\/\d{2}\/\d{2},\s\d{2}:\d{2}\s.{2}\s-\s[a-zA-Z0-9_]*:")  # extracting the date and time
        message_content = comp_sp.split(message)[1:]
        logging.info(f"Message: {message_content}")
    try:
        for ind, mat in enumerate(data_locs):
            date_form = format_dtime(f"{mat.group(1)} {mat.group(2)}")
            logging.info(date_form)
            msg = Messagestore(
                sourcemsg=source,
                msgdate=date_form,
                phonenumber=mat.group(3),
                rawcontent=message_content[ind],
            )
            msg.save()
        return {"write": "suceeded"}
    except Exception as e:
        logging.info(e)
        return {"write": "failed"}


def show_messages(request, msg_id):
    sourcemsg = get_object_or_404(Rawcontent,
                                  pk=msg_id)
    msgobjs = get_list_or_404(Messagestore,
                              sourcemsg=sourcemsg)
    obj_data = []
    for msg in msgobjs:
        obj_data.append({
            "msgdate": msg.msgdate,
            "phonenumber": msg.phonenumber,
            "rawcontent": msg.rawcontent,
            "openaiparsed": msg.openaiparsed,
            "groqparsed": msg.groqparsed,
            "id": msg.pk,
        })
    context = {"obj_data": obj_data}
    return render(request, 'show_messages.html', context)


@csrf_exempt
def store_message(request):
    if request.POST:
        dictionary = request.POST.dict()
        logging.debug(dictionary)
        message = dictionary['message']

        try:
            raw = Rawcontent(content=message)
            raw.save()
        except Exception as e:
            logging.info(f"Storing failed {e}")
            return redirect(reverse('page404'))

        write_db = msg_to_db(message, raw)
        write_db['message'] = message
        write_db['msg_id'] = raw.pk
        logging.info(write_db)
        return render(request, 'parse_message.html', write_db)
    else:
        return render(reverse('page404'))


def delete_message(request, msg_id):
    del_rawmsg = get_object_or_404(Rawcontent, pk=msg_id)
    try:
        del_rawmsg.delete()
        return redirect(reverse('post_msg'))
    except Exception as e:
        logging.info(e)
        return redirect(reverse('page404'))


def save_json(request, raw):
    raw_msg = get_object_or_404(Messagestore, pk=raw)
    json_openai = llm_text_parser(raw_msg.rawcontent)
    json_groq = llm_groq_parser(raw_msg.rawcontent)
    raw_msg.groqparsed = json_groq
    raw_msg.openaiparsed = json_openai
    try:
        raw_msg.save()
        return render(request, 'show_messages.html',
                      {"raw_msg": raw_msg,
                       "source": raw_msg.sourcemsg.pk})
    except Exception as e:
        logging.info(f'Issue in saving parsed msg. {e}')
        return redirect(reverse('page404'))


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
    match1 = search(pattern1, llm_prediction)
    if match1:
        can_do = match1.group(1).strip()
    else:
        can_do = 'Not found'
    match2 = search(pattern2, llm_prediction)
    if match2:
        language = match2.group(1).strip()
    else:
        language = 'Not Found'
    match3 = search(pattern3, llm_prediction, DOTALL)
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
        int_code_convo = ''

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
        "chlng_id": chlng_obj.id,
        "code_prompt": code_prompt,
        "snippet": code_extractor(snippet),
        "int_obj": int_obj,
        "int_code_convo": int_code_convo
    }
    return render(request, 'code_page.html', context)


def start_codechat(request, itt_id):
    # get the prompt for code generation
    int_obj = get_object_or_404(Promptintent, pk=itt_id)
    chlng_obj = get_object_or_404(Objective, pk=int_obj.objective_id)
    chlng_dict = chlng_obj.__dict__

    curr_obj_codes = Codesnippet.objects.all()

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
        int_code_convo = ''

    int_code_convo = intent_code_assembler(curr_obj_codes)
    context = {
        "chlng_id": chlng_obj.id,
        "int_obj": int_obj,
        "int_code_convo": int_code_convo,
        "curr_code_list": curr_code_list,
    }
    return render(request, 'code_page.html', context)


def page404(request):
    return render(request, 'page404.html', {"error": "error"})


def viewtest(request):
    objt_form = ObjectiveForm()
    return render(request, 'index_test.html', {'form': objt_form})