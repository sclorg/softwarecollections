from django.conf import settings
from django.http.response import Http404
from django.shortcuts import render_to_response, get_object_or_404

from django.views.generic import CreateView, DetailView
from .models import SoftwareCollection

from django.template import RequestContext

from tagging.models import Tag

from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model



def _list(request, template, queryset, dictionary, **kwargs):
    filter_params = {}
    for key in ['maturity', 'rebase_policy', 'update_freq']:
        if key in kwargs:
            filter_params[key] = kwargs[key]
    dictionary['collections'] = queryset.filter(**filter_params)
    return render_to_response(template, dictionary,
        context_instance = RequestContext(request))


def list_all(request, **kwargs):
    queryset = SoftwareCollection.objects
    return _list(request, 'scls/list_all.html', queryset, {}, **kwargs)


@login_required
def list_my(request, **kwargs):
    queryset = SoftwareCollection.objects.filter(maintainer = request.user)
    return _list(request, 'scls/list_my.html', queryset, {}, **kwargs)


def list_user(request, username, **kwargs):
    User = get_user_model()
    user = get_object_or_404(User, **{User.USERNAME_FIELD: username})
    queryset = SoftwareCollection.objects.filter(maintainer = user)
    dictionary = {'user': user}
    return _list(request, 'scls/list_user.html', queryset, dictionary, **kwargs)


def list_tag(request, name, **kwargs):
    try:
        tag = Tag.objects.get(name=name)
    except:
        tag = Tag()
        tag.name = name
    queryset = SoftwareCollection.tagged.with_all(tag)
    dictionary = {'tag': tag}
    return _list(request, 'scls/list_tag.html', queryset, dictionary, **kwargs)


class Detail(DetailView):
    model = SoftwareCollection
    context_object_name = 'scl'

detail = Detail.as_view()


class New(CreateView):
    model = SoftwareCollection

new = login_required(New.as_view())

