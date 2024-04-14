from django.urls import path
from .views import (
    index,
    pseudocode,
    intent
)


urlpatterns = [
    path("", index, name='home'),
    path("intent/", intent, name='intent'),
    path("pcode/", pseudocode, name='pcode'),
]