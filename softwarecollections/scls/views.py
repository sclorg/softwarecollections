from django.conf import settings
from django.http.response import Http404
from django.shortcuts import render
from django.template.base import TemplateDoesNotExist

from django.views.generic.list import ListView
from .models import SoftwareCollection


class SCLsList(ListView):
    model = SoftwareCollection
    paginate_by = 10

directory = SCLsList.as_view()
new       = SCLsList.as_view()

