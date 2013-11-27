from os.path import join
from django.conf import settings
from django.utils._os import safe_join
from django.http.response import Http404
from django.shortcuts import render
from django.template.base import TemplateDoesNotExist

from django.views.generic.list import ListView
from .models import SoftwareCollection


class SCLsList(ListView):
    model = SoftwareCollection


def page(request, path, template_dir=None):
    if template_dir:
        parts = [template_dir, request.LANGUAGE_CODE]
    else:
        parts = [request.LANGUAGE_CODE]
    if path:
        # add parts nice parts of path
        parts.extend([part for part in path.strip().split('/') if part not in ('','.','..')])

    template_name = '/'.join(parts) + '.html'
    try:
        return render(request, template_name)
    except TemplateDoesNotExist as e:
        if settings.DEBUG:
            raise
        else:
            raise Http404
