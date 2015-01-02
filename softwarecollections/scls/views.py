import json
from django.contrib import messages
from django.contrib.auth import get_user_model, REDIRECT_FIELD_NAME
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ObjectDoesNotExist
from django.core.mail import mail_managers
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.urlresolvers import reverse
from django.db.models import Q, Manager
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, DetailView, UpdateView
from softwarecollections.copr import CoprProxy
from tagging.models import Tag
from urllib.parse import urlsplit, urlunsplit
from libravatar import libravatar_url

from .forms import (
    FilterForm, CreateForm, UpdateForm, DeleteForm, RateForm,
    CollaboratorsForm, CoprsForm, ReposForm, ReviewReqForm, SyncReqForm,
    ComplainForm
)
from .models import Copr, SoftwareCollection, Repo, Score


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
        if filter_form.cleaned_data['policy']:
            queryset = queryset.filter(policy=filter_form.cleaned_data['policy'])
        if filter_form.cleaned_data['repo']:
            queryset = queryset.filter(
                id__in=Repo.objects.filter(
                    has_content=True,
                    name=filter_form.cleaned_data['repo']
                ).values('scl_id')
            )
        per_page = filter_form.cleaned_data['per_page'] or \
                   filter_form.fields['per_page'].initial
        order_by = filter_form.cleaned_data['order_by'] or \
                   filter_form.fields['order_by'].initial
    else:
        per_page = filter_form.fields['per_page'].initial
        order_by = filter_form.fields['order_by'].initial
    paginator = Paginator(queryset.order_by('-approved', order_by), per_page)
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
    queryset = SoftwareCollection.objects.filter(has_content=True)
    return _list(request, 'scls/list_all.html', queryset, {}, **kwargs)


@login_required
def list_my(request, **kwargs):
    queryset = request.user.softwarecollection_set
    return _list(request, 'scls/list_my.html', queryset, {}, **kwargs)


def list_user(request, username, **kwargs):
    User = get_user_model()
    user = get_object_or_404(User, **{User.USERNAME_FIELD: username})
    try:
        gravatar = libravatar_url(email=user.email, https=True)
    except IOError:
        gravatar = ""
    abc = dir(user)
    queryset = user.softwarecollection_set.filter(has_content=True)
    dictionary = {'user': user, "gravatar": gravatar}
    return _list(request, 'scls/list_user.html', queryset, dictionary, **kwargs)


def list_tag(request, name, **kwargs):
    try:
        tag = Tag.objects.get(name=name)
    except:
        tag = Tag()
        tag.name = name
    queryset = SoftwareCollection.tagged.with_all(tag).filter(has_content=True)
    dictionary = {'tag': tag}
    return _list(request, 'scls/list_tag.html', queryset, dictionary, **kwargs)


def coprnames(request, copr_username, **kwargs):
    if copr_username:
        coprnames = CoprProxy().coprnames(copr_username)
    else:
        coprnames = []
    return HttpResponse(json.dumps(sorted(coprnames)), mimetype='application/json')


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

    def get_initial(self):
        initial = {
            'maintainer': self.request.user
        }
        try:
            initial['copr_username'] = Copr.objects.filter(
                softwarecollection__maintainer=self.request.user
            ).order_by('-id')[0].username
        except:
            initial['copr_username'] = initial['maintainer'].get_username()
        return initial

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(New, self).dispatch(*args, **kwargs)

new = New.as_view()


class Edit(UpdateView):
    model = SoftwareCollection
    form_class = UpdateForm
    template_name_suffix = '_edit'
    context_object_name = 'scl'

    def get_object(self, *args, **kwargs):
        scl = super(Edit, self).get_object(*args, **kwargs)
        if self.request.user.has_perm('edit', obj=scl):
            return scl
        else:
            raise PermissionDenied()

    def form_valid(self, form):
        messages.success(self.request, _('The changes have been saved.'))
        return super(Edit, self).form_valid(form)

edit = Edit.as_view()


class Collaborators(UpdateView):
    model = SoftwareCollection
    form_class = CollaboratorsForm
    template_name_suffix = '_acl'
    context_object_name = 'scl'

    def get_object(self, *args, **kwargs):
        scl = super(Collaborators, self).get_object(*args, **kwargs)
        if self.request.user.has_perm('edit', obj=scl):
            return scl
        else:
            raise PermissionDenied()

    def form_valid(self, form):
        messages.success(self.request, _('The list of collaborators has been updated.'))
        return super(Collaborators, self).form_valid(form)

acl = Collaborators.as_view()


class Coprs(UpdateView):
    model = SoftwareCollection
    form_class = CoprsForm
    template_name_suffix = '_coprs'
    context_object_name = 'scl'

    def get_object(self, *args, **kwargs):
        scl = super(Coprs, self).get_object(*args, **kwargs)
        if self.request.user.has_perm('edit', obj=scl):
            return scl
        else:
            raise PermissionDenied()

    def form_valid(self, form):
        messages.success(self.request, _('The list of attached copr projects has been saved.'))
        return super(Coprs, self).form_valid(form)

coprs = Coprs.as_view()


class Repos(UpdateView):
    model = SoftwareCollection
    form_class = ReposForm
    template_name_suffix = '_repos'
    context_object_name = 'scl'

    def get_object(self, *args, **kwargs):
        scl = super(Repos, self).get_object(*args, **kwargs)
        if self.request.user.has_perm('edit', obj=scl):
            return scl
        else:
            raise PermissionDenied()

    def form_valid(self, form):
        messages.success(self.request, _('The list of attached Copr repositories has been saved.'))
        return super(Repos, self).form_valid(form)

repos = Repos.as_view()


class Delete(UpdateView):
    model = SoftwareCollection
    form_class = DeleteForm
    template_name_suffix = '_delete'
    context_object_name = 'scl'

    def get_object(self, *args, **kwargs):
        scl = super(Delete, self).get_object(*args, **kwargs)
        self.success_url = reverse(
            'scls:list_user',
            kwargs={"username": self.request.user.get_username()}
        )
        if self.request.user.has_perm('delete', obj=scl):
            return scl
        else:
            raise PermissionDenied()

    def form_valid(self, form):
        messages.success(self.request, _('The Collection has been deleted.'))
        return super(Delete, self).form_valid(form)

delete = Delete.as_view()


class ReviewReq(UpdateView):
    model = SoftwareCollection
    form_class = ReviewReqForm
    template_name_suffix = '_review_req'
    context_object_name = 'scl'

    def get_object(self, *args, **kwargs):
        scl = super(ReviewReq, self).get_object(*args, **kwargs)
        if self.request.user.has_perm('edit', obj=scl):
            return scl
        else:
            raise PermissionDenied()

    def form_valid(self, form):
        messages.success(self.request, _('The review has been requested.'))
        subject = _('The review has been requested for {title}') \
                    .format(title=self.object.title)
        message = _(
            'The review has been requested for {title}.\n' \
            'Collection URL: http://softwarecollections.org{url}\n' \
            'Admin URL: http://softwarecollections.org/en/admin/scls/softwarecollection/{id}/'
        ).format(title=self.object.title, url=self.object.get_absolute_url(), id=self.object.id)
        mail_managers(subject, message, fail_silently=True)
        return super(ReviewReq, self).form_valid(form)

review_req = ReviewReq.as_view()


class SyncReq(UpdateView):
    model = SoftwareCollection
    form_class = SyncReqForm
    template_name_suffix = '_sync_req'
    context_object_name = 'scl'

    def get_object(self, *args, **kwargs):
        scl = super(SyncReq, self).get_object(*args, **kwargs)
        if self.request.user.has_perm('edit', obj=scl):
            return scl
        else:
            raise PermissionDenied()

    def form_valid(self, form):
        messages.success(self.request, _('The synchronization has been requested.'))
        return super(SyncReq, self).form_valid(form)

sync_req = SyncReq.as_view()


class Complain(UpdateView):
    model = SoftwareCollection
    form_class = ComplainForm
    template_name_suffix = '_complain'
    context_object_name = 'scl'

    def form_valid(self, form):
        email = 'jdornak@redhat.com'
        
        subject = _('[{title}] {subject}').format(
            title=self.object.title,
            subject=form.cleaned_data['subject']
        )
        message = _(
            'Reporter: {email}\n' \
            'Collection: {title}\n' \
            'Message:\n{message}'
        ).format(
            email=form.cleaned_data['email'],
            title=self.object.title,
            message=form.cleaned_data['message']
        )
        mail_managers(subject, message, fail_silently=False)
        messages.success(self.request, _('Your report has been sent to administrators.'))
        return super(Complain, self).form_valid(form)

complain = Complain.as_view()


def download(request, slug):
    repo = get_object_or_404(Repo, slug=slug)
    repo.download_count+=1
    repo.save()
    repo.scl.download_count+=1
    repo.scl.save()
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

