import os
from captcha.fields import CaptchaField
from django import forms
from django.contrib.auth import get_user_model
from django.forms.forms import pretty_name
from django.forms.widgets import CheckboxFieldRenderer, RadioFieldRenderer
from django.utils.translation import ugettext_lazy as _
from django.utils.safestring import mark_safe
from softwarecollections.copr import CoprProxy
from tagging.forms import TagField

from .models import (
    SoftwareCollection, Copr, Repo, Score,
    POLICY_CHOICES_TEXT, POLICY_CHOICES_LABEL
)

PER_PAGE_CHOICES = ((10, '10'), (25, '25'), (50, '50'))

ORDER_BY_CHOICES = (
    ('-download_count', _('download count')),
    ('-score',          _('score')),
    ('title',           _('title')),
    ('-last_modified',  _('recently built')),
)


class TableRenderer:

    def render_option(self, value, label, i):
        widget = self.choice_input_class(self.name, self.value, self.attrs.copy(), (value, label), i)
        row    = '<tr><td class="col-md-1 text-center td-gray">{}</td><td><label for="{}">{}</label></td></tr>'
        return row.format(widget.tag(), widget.attrs['id'], widget.choice_label)

    def render(self):
        header  = '<div class="panel panel-default"><table class="table"><tbody>'
        group   = '<tr><th colspan="2">{}</th></tr>'
        footer  = '</tbody></table></div>'
        rows    = []
        i       = 0
        for value, label in self.choices:
            if isinstance(label, (list, tuple)):
                rows.append(group.format(value))
                for v, l in label:
                    rows.append(self.render_option(v, l, i))
                    i += 1
            else:
                rows.append(self.render_option(value, label, i))
            i += 1
        if not rows:
            rows.append('<tr><td class="col-md-1 text-center td-gray"><input type="checkbox" disabled="disabled" /></td><td></td></tr>')
        return mark_safe(
            header + '\n'.join(rows) + footer
        )


class CheckboxSelectMultipleTableRenderer(TableRenderer, CheckboxFieldRenderer):
    ''' Renders CheckboxSelectMultiple in a nice table '''


class RadioSelectTableRenderer(TableRenderer, RadioFieldRenderer):
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
        copr = Copr.objects.get_or_create(
            username = self.instance.copr_username,
            name     = self.instance.copr_name,
        )[0]
        self.instance.slug          = '{}/{}'.format(self.instance.maintainer.username, self.instance.name)
        self.instance.title         = pretty_name(self.instance.name)
        self.instance.description   = copr.description
        self.instance.instructions  = copr.instructions
        os.makedirs(self.instance.get_repos_root())
        scl = super(CreateForm, self).save(commit)
        scl.coprs.add(copr)
        scl.add_auto_tags()
        scl.collaborators.add(self.instance.maintainer)
        return scl

    class Meta:
        model = SoftwareCollection
        fields = ['copr_username', 'copr_name', 'maintainer', 'name', 'issue_tracker', 'upstream_url' ,'policy']
        widgets = {
            'copr_username': forms.TextInput( attrs={'class': 'form-control'}),
            'copr_name':     forms.Select(    attrs={'class': 'form-control'}),
            'issue_tracker': forms.TextInput( attrs={'class': 'form-control'}),
            'maintainer':    MaintainerWidget(attrs={'class': 'form-control'}),
            'name':          forms.TextInput( attrs={'class': 'form-control'}),
            'upstream_url':  forms.TextInput( attrs={'class': 'form-control'}),
            'policy':        forms.RadioSelect(renderer=RadioSelectTableRenderer),
        }


class UpdateForm(_SclForm):
    tags = TagField(required=False, help_text=_(
        'Enter space separated list of single word tags ' \
        'or comma separated list of tags containing spaces. ' \
        'Use doublequotes to enter name containing comma.'
    ), widget=forms.TextInput(attrs={'class': 'form-control'}))

    def __init__(self, *args, **kwargs):
        super(UpdateForm, self).__init__(*args, **kwargs)
        self.initial['tags'] = self.instance.tags_edit_string()

    def save(self, commit=True):
        scl = super(UpdateForm, self).save(commit)
        copr = Copr.objects.get_or_create(
            username = scl.copr_username,
            name     = scl.copr_name,
        )[0]
        scl.coprs.add(copr)
        scl.tags = self.cleaned_data['tags']
        scl.add_auto_tags()
        return scl

    class Meta:
        model = SoftwareCollection
        fields = ['title', 'description', 'instructions', 'issue_tracker', 'upstream_url', 'policy', 'copr_username', 'copr_name', 'auto_sync',]
        widgets = {
            'title':         forms.TextInput(    attrs={'class': 'form-control'}),
            'description':   forms.Textarea(     attrs={'class': 'form-control', 'rows': '4'}),
            'instructions':  forms.Textarea(     attrs={'class': 'form-control', 'rows': '4'}),
            'upstream_url':  forms.TextInput(    attrs={'class': 'form-control'}),
            'policy':        forms.RadioSelect(choices=POLICY_CHOICES_TEXT, renderer=RadioSelectTableRenderer),
            'copr_username': forms.TextInput(    attrs={'class': 'form-control'}),
            'copr_name':     forms.Select(       attrs={'class': 'form-control'}),
            'issue_tracker': forms.TextInput(    attrs={'class': 'form-control'}),
            'auto_sync':     forms.CheckboxInput(attrs={'class': 'form-control-static'}),
        }


class DeleteForm(forms.ModelForm):
    scl_name = forms.fields.CharField(required=False,
                    widget=forms.TextInput(attrs={'class': 'form-control'}))

    def clean_scl_name(self):
        if self.cleaned_data['scl_name'] != self.instance.name:
            raise forms.ValidationError(_('Enter the name of your collection.'))
        return self.cleaned_data['scl_name']

    def save(self, commit=True):
        scl = super(DeleteForm, self).save(commit)
        scl.delete()
        return scl

    class Meta:
        model = SoftwareCollection
        fields = []


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

    class Meta:
        model = SoftwareCollection
        fields = ['collaborators']
        widgets = {
            'collaborators': forms.CheckboxSelectMultiple(renderer=CheckboxSelectMultipleTableRenderer)
        }


class ReposForm(forms.ModelForm):
    repos = forms.MultipleChoiceField(label=_('Enabled repos'),
                widget=forms.widgets.CheckboxSelectMultiple(renderer=CheckboxSelectMultipleTableRenderer))

    def __init__(self, *args, **kwargs):
        super(ReposForm, self).__init__(*args, **kwargs)
        self.initial['repos'] = [
            '{}/{}/{}'.format(repo.copr.username, repo.copr.name, repo.name)
            for repo in self.instance.all_repos
        ]
        self.fields['repos'].choices = [
            (
                copr.slug, 
                [
                    (
                        '{}/{}/{}'.format(repo.copr.username, repo.copr.name, repo.name),
                        mark_safe('<img src="{}" width="32" height="32" alt=""/> {} {} {}'.format(
                            repo.get_icon_url(), repo.distro.title(), repo.version, repo.arch
                        )),
                    ) for repo in [
                        Repo(
                            scl      = self.instance,
                            copr     = copr,
                            name     = name,
                            copr_url = url,
                        ) for name, url in copr.yum_repos.items()
                    ]
                ]
            ) for copr in self.instance.all_coprs
        ]

    def save(self, commit=True):
        scl   = super(ReposForm, self).save(False)
        coprs = dict((copr.slug, copr) for copr in scl.all_coprs)
        ids   = []
        for r in self.cleaned_data['repos']:
            slug, name = r.rsplit('/',1)
            copr = coprs[slug]
            ids.append(
                Repo.objects.get_or_create(
                    scl=scl,
                    copr=copr,
                    name=name,
                    copr_url=copr.yum_repos[name],
                )[0].id
            )
        for repo in scl.repos.exclude(id__in=ids):
            repo.delete()
        del(scl._all_repos)
        scl.add_auto_tags()
        return scl

    class Meta:
        model = SoftwareCollection
        fields = []


class ReviewReqForm(forms.ModelForm):

    def clean_review_req(self):
        return True

    class Meta:
        model = SoftwareCollection
        fields = ['review_req']
        widgets = {
            'review_req': forms.HiddenInput(),
        }


class SyncReqForm(forms.ModelForm):

    def clean_need_sync(self):
        return True

    class Meta:
        model = SoftwareCollection
        fields = ['need_sync']
        widgets = {
            'need_sync': forms.HiddenInput(),
        }


class ComplainForm(forms.ModelForm):
    email   = forms.EmailField(
                widget=forms.EmailInput(attrs={'class': 'form-control'}))
    subject = forms.CharField(
                widget=forms.TextInput(attrs={'class': 'form-control'}))
    message = forms.CharField(
                widget=forms.Textarea(attrs={'class': 'form-control', 'rows': '6'}))
    captcha = CaptchaField()

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
    search      = forms.CharField(required=False, max_length=999,
                    widget=forms.TextInput(attrs={'class': 'form-control',
                        'placeholder': 'Search Text'}))
    search_desc = forms.BooleanField(required=False, label='search description')
    approved    = forms.BooleanField(required=False,
                    help_text='Display only collections, which have passed a review.')
    per_page    = forms.ChoiceField(required=False, label='Per page',
                    initial=PER_PAGE_CHOICES[0][0],
                    choices=PER_PAGE_CHOICES,
                    widget=forms.Select(attrs={'class': 'form-control'}))
    order_by    = forms.ChoiceField(required=False, label='Order',
                    initial=ORDER_BY_CHOICES[0][0],
                    choices=ORDER_BY_CHOICES,
                    widget=forms.Select(attrs={'class': 'form-control'}))
    policy      = forms.ChoiceField(required=False, label='Policy',
                    choices=[('', 'All')] + POLICY_CHOICES_LABEL,
                    widget=forms.Select(attrs={'class': 'form-control'}))
    repo        = forms.ChoiceField(required=False, label='Repository',
                    widget=forms.Select(attrs={'class': 'form-control'}))

    def __init__(self, *args, **kwargs):
        super(FilterForm, self).__init__(*args, **kwargs)
        self.fields['repo'].choices = [('', 'All')] + list(
            map(
                lambda r: (r['name'], r['name'].capitalize().replace('-', ' ', 1).replace('-', ' - ')),
                Repo.objects.values('name').distinct()
            )
        )

