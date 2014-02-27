import os
from django import forms
from django.contrib.auth import get_user_model
from django.forms.forms import pretty_name
from django.utils.translation import ugettext_lazy as _
from softwarecollections.copr import CoprProxy
from tagging.forms import TagField

from .models import SoftwareCollection, Score, POLICY_CHOICES

PER_PAGE_CHOICES = ((10, '10'), (25, '25'), (50, '50'))

ORDER_BY_CHOICES = (
    ('-score',          _('score')),
    ('title',           _('title')),
    ('-download_count', _('download count')),
    ('-last_modified',  _('recently built')),
)


class CreateForm(forms.ModelForm):

    def __init__(self, request, **kwargs):
        self.request = request
        super(CreateForm, self).__init__(**kwargs)
        if 'copr_username' in self.request.REQUEST:
            copr_username = self.request.REQUEST['copr_username']
        else:
            try:
                copr_username = SoftwareCollection.objects.filter(
                    maintainer=self.request.user
                ).order_by('-id')[0].copr_username
            except:
                copr_username = self.request.user.get_username()
        self.initial['copr_username'] = copr_username
        self.initial['maintainer']    = self.request.user
        if copr_username:
            coprnames = CoprProxy().coprnames(copr_username)
        else:
            coprnames = []
        copr_name_choices = tuple((name, name) for name in coprnames)
        self.fields['copr_name'].widget.choices = copr_name_choices

    def save(self, commit=True):
        obj = super(CreateForm, self).save(False)
        obj.maintainer = self.request.user
        obj.slug       = '{}/{}'.format(obj.maintainer.username, obj.name)
        obj.title      = pretty_name(obj.name)
        obj.sync_copr_texts()
        os.makedirs(obj.get_repos_root())
        obj.save()
        obj.sync_copr_repos()
        obj.add_auto_tags()
        obj.collaborators.add(obj.maintainer)
        return obj

    class Meta:
        model = SoftwareCollection
        fields = ['copr_username', 'copr_name', 'maintainer', 'name', 'policy']
        widgets = {
            'copr_name': forms.Select(),
            'maintainer': forms.HiddenInput(),
            'policy': forms.RadioSelect(),
        }


class UpdateForm(forms.ModelForm):
    tags = TagField(max_length=200, required=False, help_text=_(
        'Enter space separated list of single word tags ' \
        'or comma separated list of tags containing spaces. ' \
        'Use doublequotes to enter name containing comma.'
    ))

    def __init__(self, request, **kwargs):
        self.request = request
        super(UpdateForm, self).__init__(**kwargs)
        if 'copr_username' in self.request.REQUEST:
            copr_username = self.request.REQUEST['copr_username']
        else:
            copr_username = self.instance.copr_username
        coprnames = CoprProxy().coprnames(copr_username)
        copr_name_choices = tuple((name, name) for name in coprnames)
        self.fields['copr_name'].widget.choices = copr_name_choices
        self.initial['tags'] = self.instance.tags_edit_string()

    def save(self, commit=True):
        obj = super(UpdateForm, self).save(commit)
        obj.tags = self.cleaned_data['tags']
        obj.sync_copr_repos()
        obj.add_auto_tags()
        return obj

    class Meta:
        model = SoftwareCollection
        fields = ['title', 'description', 'instructions', 'policy', 'copr_username', 'copr_name', 'auto_sync']
        widgets = {
            'policy': forms.RadioSelect(),
            'copr_name': forms.Select(),
        }


class CollaboratorsForm(forms.ModelForm):
    add = forms.fields.CharField(required=False)

    def __init__(self, *args, **kwargs):
        super(CollaboratorsForm, self).__init__(*args, **kwargs)
        self.fields['collaborators'].widget.choices = tuple(
            map(
                lambda u: (u.id, '{} ({})'.format(u.get_full_name(), u.get_username())),
                filter(
                    lambda u: u != self.instance.maintainer,
                    self.instance.collaborators.all()
                )
            )
        )

    def clean(self):
        self.cleaned_data = super(CollaboratorsForm, self).clean()
        self.cleaned_data['collaborators'] = list(self.cleaned_data['collaborators'])
        add = self.cleaned_data.pop('add')
        if add:
            try:
                self.cleaned_data['collaborators'].append(
                    get_user_model().objects.get(username=add)
                )
            except:
                self.errors['add'] = [_('Unknown user')]
        self.cleaned_data['collaborators'].append(self.instance.maintainer)
        return self.cleaned_data

    def save(self, commit=True):
        obj = super(CollaboratorsForm, self).save(commit)
        obj.add_auto_tags()
        return obj

    class Meta:
        model = SoftwareCollection
        fields = ['collaborators']
        widgets = {
            'collaborators': forms.CheckboxSelectMultiple()
        }


class RateForm(forms.ModelForm):

    class Meta:
        model = Score
        fields = ['score']
        widgets = {
            'score': forms.HiddenInput(),
        }


class FilterForm(forms.Form):
    search          = forms.CharField(required=False, max_length=999)
    search_desc     = forms.BooleanField(required=False)
    approved        = forms.BooleanField(required=False)
    per_page        = forms.ChoiceField(required=False,
                        initial=PER_PAGE_CHOICES[0][0],
                        choices=PER_PAGE_CHOICES)
    order_by        = forms.ChoiceField(required=False,
                        initial=ORDER_BY_CHOICES[0][0],
                        choices=ORDER_BY_CHOICES)

