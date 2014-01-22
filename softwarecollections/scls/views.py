from django.contrib import messages
from django.contrib.auth import get_user_model, REDIRECT_FIELD_NAME
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ObjectDoesNotExist
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, Manager
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, DetailView, UpdateView
from tagging.models import Tag
from urllib.parse import urlsplit, urlunsplit

from .forms import FilterForm, CreateForm, UpdateForm, RateForm
from .models import SoftwareCollection, Repo, Score


def _list(request, template, queryset, dictionary, **kwargs):
    filter_form   = FilterForm(data=request.GET)
    if filter_form.is_valid():
        if filter_form.cleaned_data['search']:
            search = Q()
            for word in filter_form.cleaned_data['search'].split():
                search |= Q(name__contains=word) | Q(title__contains=word)
                if filter_form.cleaned_data['search_desc']:
                    search |= Q(description__contains=word)
            queryset = queryset.filter(search)
        if filter_form.cleaned_data['approved']:
            queryset = queryset.filter(approved=True)
        per_page = filter_form.cleaned_data['per_page'] or \
                   filter_form.fields['per_page'].initial
    else:
        per_page = filter_form.fields['per_page'].initial
    if isinstance(queryset, Manager):
        queryset = queryset.all()
    paginator = Paginator(queryset, per_page)
    page = request.GET.get('page')
    try:
        collections = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        collections = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        collections = paginator.page(paginator.num_pages)
    dictionary['collections'] = collections
    dictionary['filter_form'] = filter_form
    dictionary['paginator']   = paginator
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
    form_class = CreateForm
    template_name_suffix = '_new'

    def get_form_kwargs(self):
        kwargs = super(New, self).get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(New, self).dispatch(*args, **kwargs)

new = New.as_view()


class Edit(UpdateView):
    model = SoftwareCollection
    form_class = UpdateForm
    template_name_suffix = '_edit'

    def get_object(self, *args, **kwargs):
        scl = super(Edit, self).get_object(*args, **kwargs)
        if self.request.user.has_perm('edit', obj=scl):
            return scl
        else:
            raise PermissionDenied()

edit = Edit.as_view()


def app_req(request, slug):
    scl = get_object_or_404(SoftwareCollection, slug=slug)
    if scl.approved or scl.approval_req or not request.user.has_perm('edit', obj=scl):
        raise PermissionDenied()
    scl.approval_req = True
    scl.save()
    messages.success(request, 'Approval requested.')
    return HttpResponseRedirect(scl.get_absolute_url())


def sync_req(request, slug):
    scl = get_object_or_404(SoftwareCollection, slug=slug)
    if scl.auto_sync or scl.need_sync or not request.user.has_perm('edit', obj=scl):
        raise PermissionDenied()
    scl.need_sync = True
    scl.save()
    messages.success(request, 'Synchronization with Copr repositories requested.')
    return HttpResponseRedirect(scl.get_absolute_url())


def download(request, slug):
    repo = get_object_or_404(Repo, slug=slug)
    repo.download_count+=1
    repo.save()
    return HttpResponseRedirect(repo.get_rpmfile_url())


@require_POST
def rate(request, slug):
    scl = get_object_or_404(SoftwareCollection, slug=slug)
    if not request.user.has_perm('rate', obj=scl):
        raise PermissionDenied()
    form = RateForm(data=request.POST)
    if form.is_valid():
        data = form.cleaned_data
        try:
            score = Score.objects.get(user=request.user, scl=scl)
        except ObjectDoesNotExist:
            score = Score(user=request.user, scl=scl)
        score.score = data['score']
        score.save()
    else:
        for message in form.errors.values():
            messages.error(request, message)
    return HttpResponseRedirect(scl.get_absolute_url())

