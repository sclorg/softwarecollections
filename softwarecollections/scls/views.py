from django.contrib import messages
from django.contrib.auth import get_user_model, REDIRECT_FIELD_NAME
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ObjectDoesNotExist
from django.forms.forms import pretty_name
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, DetailView, UpdateView
from softwarecollections.copr import CoprProxy
from tagging.models import Tag
from urllib.parse import urlsplit, urlunsplit

from .forms import CreateForm, UpdateForm, RateForm
from .models import SoftwareCollection, Score


def _list(request, template, queryset, dictionary, **kwargs):
    filter_params = {}
    # TODO add filtering
    dictionary['collections'] = queryset.filter(**filter_params)
    return render_to_response(template, dictionary,
        context_instance = RequestContext(request))


def list_all(request, **kwargs):
    queryset = SoftwareCollection.objects
    return _list(request, 'scls/list_all.html', queryset, {}, **kwargs)


@login_required
def list_my(request, **kwargs):
    queryset = request.user.softwarecollection_set
    return _list(request, 'scls/list_my.html', queryset, {}, **kwargs)


def list_user(request, username, **kwargs):
    User = get_user_model()
    user = get_object_or_404(User, **{User.USERNAME_FIELD: username})
    queryset = user.softwarecollection_set
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

    def get_context_data(self, **kwargs):
        context = dict(super(Detail, self).get_context_data(**kwargs))
        if self.request.user.has_perm('rate', obj=self.object):
            try:
                context['user_score'] = Score.objects.get(user=self.request.user, scl=self.object).score
            except ObjectDoesNotExist:
                context['user_score'] = 0
        return context

detail = Detail.as_view()


class New(CreateView):
    model = SoftwareCollection
    template_name_suffix = '_new'

    def get_form_class(self):
        return CreateForm

    def form_valid(self, form):
        """
        If the form is valid, save the associated model.
        """
        self.object = form.save(commit=False)
        self.object.maintainer = self.request.user
        self.object.name       = self.object.copr_name
        self.object.title      = pretty_name(self.object.name)
        self.object.sync_copr_texts()
        self.object.save()
        self.object.sync_copr_repos()
        return super(New, self).form_valid(form)

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(New, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = dict(super(New, self).get_context_data(**kwargs))
        username = self.request.user.get_username()
        copr_proxy = CoprProxy()
        coprs = copr_proxy.coprs(username)
        context['coprs'] = coprs
        return context

new = New.as_view()

class Edit(UpdateView):
    model = SoftwareCollection
    template_name_suffix = '_edit'

    def get_object(self, *args, **kwargs):
        scl = super(Edit, self).get_object(*args, **kwargs)
        if self.request.user.has_perm('edit', obj=scl):
            return scl
        else:
            raise PermissionDenied()

    def get_form_class(self):
        return UpdateForm

    def form_valid(self, form):
        """
        If the form is valid, save the associated model.
        """
        self.object = form.save()
        self.object.tags = form.cleaned_data['tags']
        return super(Edit, self).form_valid(form)

edit = Edit.as_view()


@require_POST
def rate(request, redirect_field_name=REDIRECT_FIELD_NAME):
    form = RateForm(data=request.POST)
    if form.is_valid():
        data = form.cleaned_data
        if not request.user.has_perm('rate', obj=data['scl']):
            raise PermissionDenied()
        try:
            score = Score.objects.get(user=request.user, scl=data['scl'])
        except ObjectDoesNotExist:
            score = Score(user=request.user, scl=data['scl'])
        score.score = data['score']
        score.save()
    else:
        for message in form.errors.values():
            messages.error(request, message)
    try:
        # get safe url from user input
        url = request.REQUEST[redirect_field_name]
        url = urlunsplit(('','')+urlsplit(url)[2:])
    except:
        try:
            url = score.scl.get_absolute_url()
        except:
            url = '/'
    return HttpResponseRedirect(url)


