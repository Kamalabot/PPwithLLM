from django.forms import ModelForm
from .models import Objective


class ObjectiveForm(ModelForm):
    required_css_class = "float-right"
    class Meta:
        model = Objective
        fields = ['challenge', 'language', 'apptype', 'experience']
