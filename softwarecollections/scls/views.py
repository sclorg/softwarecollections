from django.conf import settings
from django.http.response import Http404
from django.shortcuts import render, get_object_or_404
from django.template.base import TemplateDoesNotExist

from django.views.generic import CreateView, DetailView, ListView
from .models import SoftwareCollection

from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model

User = get_user_model()


class Roster(ListView):
    view = None
    model = SoftwareCollection
    paginate_by = 10

    def get_queryset(self):
        if   self.view == 'all':
            return self.model._default_manager.all()
        elif self.view == 'my':
            return self.model._default_manager.filter(maintainer = self.request.user)
        elif self.view == 'user':
            user = get_object_or_404(User, **{User.USERNAME_FIELD: self.kwargs['username']}) 
            return self.model._default_manager.filter(maintainer = user)

all  = Roster.as_view(view='all')
my   = login_required(Roster.as_view(view='my'))
user = Roster.as_view(view='user')


class Detail(DetailView):
    model = SoftwareCollection
    context_object_name = 'scl'

detail = Detail.as_view()


class New(CreateView):
    model = SoftwareCollection

new = login_required(New.as_view())

