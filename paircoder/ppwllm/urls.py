from django.urls import path
from .views import (
    intent,
    viewtest,
    challenge_index,
    load_challenge
)


urlpatterns = [
    path("", challenge_index, name='home'),
    path("intent/", intent, name='intent'),
    path("vtest/", viewtest, name='vtest'),
    path("load_chlng/<int:chlng_id>/", load_challenge, name='load_chlng')
]
