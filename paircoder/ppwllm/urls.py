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
)

urlpatterns = [
    path("", challenge_index, name='home'),
    path("new_chlng", new_challenge, name="new_chlng"),
    path("save_chlng/", save_challenge, name='save'),
    path("del_chlng/<int:chlng_id>", delete_challenge, name='del'),
    path("intent/<int:chlng_id>", intent, name='intent'),
    path("vtest/", viewtest, name='vtest'),
    path("load_chlng/<int:chlng_id>/", load_challenge, name='load_chlng'),
    path("page404/", page404, name='page404'),
]
