from django.conf import settings
from django.http.response import Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.utils.decorators import method_decorator

from django.views.generic import CreateView, DetailView, UpdateView
from .models import SoftwareCollection
from .forms import CreateForm, UpdateForm

from django.template import RequestContext

from tagging.models import Tag

from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model



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
        self.object.save()
        return super(New, self).form_valid(form)

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(ProtectedView, self).dispatch(*args, **kwargs)

new = New.as_view()


class Edit(UpdateView):
    model = SoftwareCollection
    template_name_suffix = '_edit'

    def get_object(self, *args, **kwargs):
        scl = super(Edit, self).get_object(*args, **kwargs)
        if scl.has_perm(self.request.user, 'edit'):
            return scl
        else:
            raise PermissionDenied()

    def get_form_class(self):
        return UpdateForm

edit = Edit.as_view()

