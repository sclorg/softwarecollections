import os
from django import forms
from django.contrib.auth import get_user_model
from django.forms.forms import pretty_name
from django.utils.translation import ugettext_lazy as _
from django.utils.safestring import mark_safe
from softwarecollections.copr import CoprProxy
from tagging.forms import TagField

from .models import (
    SoftwareCollection, Repo, Score,
    POLICY_CHOICES_TEXT, POLICY_CHOICES_LABEL
)

PER_PAGE_CHOICES = ((10, '10'), (25, '25'), (50, '50'))

ORDER_BY_CHOICES = (
    ('-score',          _('score')),
    ('title',           _('title')),
    ('-download_count', _('download count')),
    ('-last_modified',  _('recently built')),
)


class TableRenderer:

    def render(self):
        header = '<div class="panel panel-default"><table class="table"><tbody>'
        row    = '<tr><td class="col-md-1 text-center td-gray">{}</td><td><label for="{}">{}</label></td></tr>'
        footer = '</tbody></table></div>'
        rows   = [row.format(w.tag(), w.attrs['id'], w.choice_label) for w in self]
        if not rows:
            rows.append('<tr><td class="col-md-1 text-center td-gray"><input type="checkbox" disabled="disabled" /></td><td></td></tr>')
        return mark_safe(
            header + '\n'.join(rows) + footer)


class CheckboxSelectMultipleTableRenderer(TableRenderer, forms.CheckboxSelectMultiple.renderer):
    ''' Renders CheckboxSelectMultiple in a nice table '''


class RadioSelectTableRenderer(TableRenderer, forms.RadioSelect.renderer):
    ''' Renders RadioSelect in a nice table '''


class MaintainerWidget(forms.HiddenInput):
    ''' Renders Maintainer '''

    def render(self, name, value, attrs=None):
        user = get_user_model().objects.get(id=value)
        html = super(MaintainerWidget, self).render(name, value, attrs=None)
        html += '\n<div class="form-control">{} ({})</div>'.format(user.get_full_name(), user.get_username())
        return mark_safe(html)


class _SclForm(forms.ModelForm):

    def __init__(self, request, **kwargs):
        self.request = request
        super(_SclForm, self).__init__(**kwargs)
        if 'copr_username' in self.request.REQUEST:
            copr_username = self.request.REQUEST['copr_username']
        elif self.instance.copr_username:
            copr_username = self.instance.copr_username
        else:
            try:
                copr_username = SoftwareCollection.objects.filter(
                    maintainer=self.request.user
                ).order_by('-id')[0].copr_username
            except:
                copr_username = self.request.user.get_username()
            self.initial['copr_username'] = copr_username
        self.initial['copr_username'] = copr_username
        self.initial['maintainer']    = self.request.user
        if copr_username:
            self.coprnames = CoprProxy().coprnames(copr_username)
        else:
            self.coprnames = []
        copr_name_choices = tuple((name, name) for name in self.coprnames)
        self.fields['copr_name'].widget.choices = copr_name_choices

    def clean_copr_username(self):
        if not len(self.coprnames):
            raise forms.ValidationError(_('No SCL project found for this Copr user.'))
        return self.cleaned_data['copr_username']

    def clean_maintainer(self):
        return self.request.user

    def clean_copr_name(self):
        if self.coprnames and self.cleaned_data['copr_name'] not in self.coprnames:
            raise forms.ValidationError(_('This field is mandatory.'))
        return self.cleaned_data['copr_name']


class CreateForm(_SclForm):

    def save(self, commit=True):
        obj = super(CreateForm, self).save(False)
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
            'copr_username': forms.TextInput( attrs={'class': 'form-control'}),
            'copr_name':     forms.Select(    attrs={'class': 'form-control'}),
            'maintainer':    MaintainerWidget(attrs={'class': 'form-control'}),
            'name':          forms.TextInput( attrs={'class': 'form-control'}),
            'policy':        forms.RadioSelect(choices=POLICY_CHOICES_TEXT,
                                                renderer=RadioSelectTableRenderer),
        }


class UpdateForm(_SclForm):
    tags = TagField(max_length=200, required=False, help_text=_(
        'Enter space separated list of single word tags ' \
        'or comma separated list of tags containing spaces. ' \
        'Use doublequotes to enter name containing comma.'
    ), widget=forms.TextInput(attrs={'class': 'form-control'}))

    def __init__(self, *args, **kwargs):
        super(UpdateForm, self).__init__(*args, **kwargs)
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
            'title':         forms.TextInput(    attrs={'class': 'form-control'}),
            'description':   forms.Textarea(     attrs={'class': 'form-control', 'rows': '4'}),
            'instructions':  forms.Textarea(     attrs={'class': 'form-control', 'rows': '4'}),
            'policy':        forms.RadioSelect(choices=POLICY_CHOICES_TEXT, renderer=RadioSelectTableRenderer),
            'copr_username': forms.TextInput(    attrs={'class': 'form-control'}),
            'copr_name':     forms.Select(       attrs={'class': 'form-control'}),
            'auto_sync':     forms.CheckboxInput(attrs={'class': 'form-control-static'}),
        }


class CollaboratorsForm(forms.ModelForm):
    add = forms.fields.CharField(required=False,
            help_text=_('Enter username of user You want to add.'))

    def __init__(self, *args, **kwargs):
        super(CollaboratorsForm, self).__init__(*args, **kwargs)
        self.fields['add'].widget.attrs={'class': 'form-control'}
        self.fields['collaborators'].help_text = _('Unselect users You want to remove.')
        self.fields['collaborators'].choices = tuple(
            map(
                lambda u: (u.id, '{} ({})'.format(u.get_full_name(), u.get_username())),
                filter(
                    lambda u: u != self.instance.maintainer,
                    self.instance.collaborators.all()
                )
            )
        )
        self.tags = self.instance.tags_edit_string()

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
        scl = super(CollaboratorsForm, self).save(commit)
        scl.tags = self.tags
        scl.add_auto_tags()
        return obj

    class Meta:
        model = SoftwareCollection
        fields = ['collaborators']
        widgets = {
            'collaborators': forms.CheckboxSelectMultiple(renderer=CheckboxSelectMultipleTableRenderer)
        }


class ReposForm(forms.ModelForm):
    repos = forms.MultipleChoiceField(label=_('Enabled repos'), required=False,
                widget=forms.widgets.CheckboxSelectMultiple(renderer=CheckboxSelectMultipleTableRenderer))

    def __init__(self, *args, **kwargs):
        super(ReposForm, self).__init__(*args, **kwargs)
        self.initial['repos'] = list(map(lambda r: r.id, self.instance.enabled_repos.all()))
        self.fields['repos'].choices = tuple(
            map(
                lambda r: (r.id, mark_safe('<img src="{}" width="32" height="32" alt=""/> {} {} {}'.format(
                    r.get_icon_url(), r.distro, r.version, r.arch
                ))),
                self.instance.repos.all()
            )
        )
        self.tags = self.instance.tags_edit_string()

    def save(self, commit=True):
        scl  = super(ReposForm, self).save(False)
        scl.repos.filter (id__in=self.cleaned_data['repos']).update(enabled=True)
        scl.repos.exclude(id__in=self.cleaned_data['repos']).update(enabled=False)
        scl.tags = self.tags
        scl.add_auto_tags()
        return scl

    class Meta:
        model = SoftwareCollection
        fields = []


class RateForm(forms.ModelForm):

    class Meta:
        model = Score
        fields = ['score']
        widgets = {
            'score': forms.HiddenInput(),
        }


class FilterForm(forms.Form):
    search          = forms.CharField(required=False, max_length=999,
                        widget=forms.TextInput(attrs={'class': 'form-control',
                            'placeholder': 'Search Text'}))
    search_desc     = forms.BooleanField(required=False, label='search description')
    approved        = forms.BooleanField(required=False, label='Approved')
    per_page        = forms.ChoiceField(required=False, label='Per page',
                        initial=PER_PAGE_CHOICES[0][0],
                        choices=PER_PAGE_CHOICES,
                        widget=forms.Select(attrs={'class': 'form-control'}))
    order_by        = forms.ChoiceField(required=False, label='Order',
                        initial=ORDER_BY_CHOICES[0][0],
                        choices=ORDER_BY_CHOICES,
                        widget=forms.Select(attrs={'class': 'form-control'}))
    policy          = forms.ChoiceField(required=False, label='Policy',
                        choices=[('', 'All')] + POLICY_CHOICES_LABEL,
                        widget=forms.Select(attrs={'class': 'form-control'}))
