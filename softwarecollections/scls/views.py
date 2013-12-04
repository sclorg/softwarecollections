from django.conf import settings
from django.http.response import Http404
from django.shortcuts import render
from django.template.base import TemplateDoesNotExist

from django.views.generic import CreateView, DetailView, ListView
from .models import SoftwareCollection


class Roster(ListView):
    model = SoftwareCollection
    paginate_by = 10

roster = Roster.as_view()


class Detail(DetailView):
    model = SoftwareCollection

detail = Detail.as_view()


class New(CreateView):
    model = SoftwareCollection

new = New.as_view()

