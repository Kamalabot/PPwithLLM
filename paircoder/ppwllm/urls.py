from django.urls import path
from .views import (
    intent,
    viewtest,
    challenge_index,
    load_challenge,
    new_challenge,
    save_challenge,
    page404,
    delete_challenge,
    delete_intent,
    delete_snippet,
    post_message,
    show_messages,
    save_json,
    store_message,
    delete_message,
    begin_coding,
    generate_code,
)

urlpatterns = [
    path("", challenge_index, name='home'),
    path("new_chlng", new_challenge, name="new_chlng"),
    path("save_chlng/", save_challenge, name='save'),
    path("del_chlng/<int:chlng_id>", delete_challenge, name='del'),
    path("intent/<int:chlng_id>", intent, name='intent'),
    path("rem_int/<int:itt_id>", delete_intent, name='rem_int'),
    path("vtest/", viewtest, name='vtest'),
    path("load_chlng/<int:chlng_id>/", load_challenge, name='load_chlng'),
    path("page404/", page404, name='page404'),
    path('post_msg', post_message, name='post_msg'),
    path('save_json/<int:raw>', save_json, name='save_json'),
    path('store_msg', store_message, name='store_msg'),
    path('remove_msg<int:msg_id>', delete_message, name='remove_msg'),
    path('show_msg/<int:msg_id>', show_messages, name='show_msg'),
    path('begin_code/<int:chlng_id>', begin_coding, name='begin_code'),
    path('gen_code/<int:itt_id>', generate_code, name='gen_code'),
    path('del_code/<int:sn_id>', delete_snippet, name='del_code'),
]
