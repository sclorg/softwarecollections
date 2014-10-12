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

PER_PAGE_CHOICES = ((10, '10 per page'), (25, '25 per page'), (50, '50 per page'))

ORDER_BY_CHOICES = (
    ('-download_count', _('Sort: download count')),
    ('-score',          _('Sort: score')),
    ('title',           _('Sort: title')),
    ('-last_modified',  _('Sort: recently built')),
)


class TableRenderer:

    def render_option(self, value, label, i):
        widget = self.choice_input_class(self.name, self.value, self.attrs.copy(), (value, label), i)
        row    = '<tr><td class="col-md-1 text-center td-gray">{}</td><td><label style="font-weight:normal" for="{}">{}</label></td></tr>'
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



class _CoprForm(forms.ModelForm):
    copr_username   = forms.CharField(label=_('Copr User'),
                        widget=forms.TextInput(attrs={'class': 'form-control'}),
                        help_text=_('Username of Copr user (Note that the packages must be built in Copr.)'))
    copr_name       = forms.ChoiceField(label=_('Copr Project'),
                        widget=forms.Select(attrs={'class': 'form-control'}),
                        help_text=_('Name of Copr Project to attach'))

    def __init__(self, **kwargs):
        super(_CoprForm, self).__init__(**kwargs)
        try:
            copr_username = kwargs['data']['copr_username']
        except:
            try:
                copr_username = kwargs['initial']['copr_username']
            except:
                copr_username = ''
        if copr_username:
            self.coprnames = CoprProxy().coprnames(copr_username)
        else:
            self.coprnames = []
        self.fields['copr_name'].choices = tuple(
            (name, name) for name in sorted(self.coprnames)
        )

    def clean_copr_username(self):
        if self.fields['copr_username' ].required and not self.coprnames:
            raise forms.ValidationError(_('No SCL project found for this Copr user.'))
        return self.cleaned_data['copr_username']

    def clean_copr_name(self):
        if self.fields['copr_username' ].required and self.coprnames \
            and self.cleaned_data['copr_name'] not in self.coprnames:
            raise forms.ValidationError(_('This field is mandatory.'))
        return self.cleaned_data['copr_name']

    def clean(self):
        self.cleaned_data = super(_CoprForm, self).clean()
        if self.cleaned_data['copr_username'] and self.cleaned_data['copr_name']:
            self.cleaned_data['copr'] = Copr.objects.get_or_create(
                username  = self.cleaned_data['copr_username'],
                name      = self.cleaned_data['copr_name'],
            )[0]
            if 'coprs' in self.cleaned_data:
                self.cleaned_data['coprs'] = list(self.cleaned_data['coprs'])
                self.cleaned_data['coprs'].append(self.cleaned_data['copr'])
        return self.cleaned_data



class CreateForm(_CoprForm):

    def clean_maintainer(self):
        """
        We need to include maintainer field
        (for unique check of maintainer/name pair)
        but we do not allow user to change it
        """
        return self.initial['maintainer']

    def save(self, commit=True):
        self.instance.slug          = '{}/{}'.format(self.instance.maintainer.get_username(), self.instance.name)
        self.instance.title         = pretty_name(self.instance.name)
        self.instance.description   = self.cleaned_data['copr'].description
        self.instance.instructions  = self.cleaned_data['copr'].instructions
        os.makedirs(self.instance.get_repos_root())
        self.instance.save()
        self.instance.coprs.add(self.cleaned_data['copr'])
        self.instance.add_auto_tags()
        self.instance.collaborators.add(self.instance.maintainer)
        return self.instance

    class Meta:
        model = SoftwareCollection
        fields = ['copr_username', 'copr_name', 'maintainer', 'name', 'issue_tracker', 'upstream_url' ,'policy']
        widgets = {
            'issue_tracker': forms.TextInput( attrs={'class': 'form-control'}),
            'maintainer':    MaintainerWidget(attrs={'class': 'form-control'}),
            'name':          forms.TextInput( attrs={'class': 'form-control'}),
            'upstream_url':  forms.TextInput( attrs={'class': 'form-control'}),
            'policy':        forms.RadioSelect(renderer=RadioSelectTableRenderer),
        }


class UpdateForm(forms.ModelForm):
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
        scl.tags = self.cleaned_data['tags']
        scl.add_auto_tags()
        return scl

    class Meta:
        model = SoftwareCollection
        fields = ['title', 'description', 'instructions', 'issue_tracker', 'upstream_url', 'policy', 'auto_sync',]
        widgets = {
            'title':         forms.TextInput(    attrs={'class': 'form-control'}),
            'description':   forms.Textarea(     attrs={'class': 'form-control', 'rows': '4'}),
            'instructions':  forms.Textarea(     attrs={'class': 'form-control', 'rows': '4'}),
            'upstream_url':  forms.TextInput(    attrs={'class': 'form-control'}),
            'policy':        forms.RadioSelect(choices=POLICY_CHOICES_TEXT, renderer=RadioSelectTableRenderer),
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
            widget=forms.TextInput(attrs={'class': 'form-control'}),
            help_text=_('Enter username of user You want to add.'))

    def __init__(self, *args, **kwargs):
        super(CollaboratorsForm, self).__init__(*args, **kwargs)
        self.fields['collaborators'].help_text = _('Unselect users You want to remove.')
        self.fields['collaborators'].choices = tuple(
            (u.id, '{} ({})'.format(u.get_full_name(), u.get_username()))
            for u in self.instance.all_collaborators
            if  u != self.instance.maintainer
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


class CoprsForm(_CoprForm):

    def __init__(self, *args, **kwargs):
        super(CoprsForm, self).__init__(*args, **kwargs)
        self.fields['copr_username'].required = False
        self.fields['copr_name'    ].required = False
        self.fields['coprs'].help_text = _('Unselect Copr projects You want to remove.')
        self.fields['coprs'].choices = tuple(
            (copr.id, '{} / {}'.format(copr.username, copr.name))
            for copr in self.instance.all_coprs
        )

    def save(self, commit=True):
        scl = super(CoprsForm, self).save()
        del(scl.all_coprs)
        del(scl.all_repos)
        for repo in self.instance.repos.exclude(copr__in=scl.coprs.all()):
            repo.delete()
        scl.add_auto_tags()
        return scl

    class Meta:
        model = SoftwareCollection
        fields = ['coprs']
        widgets = {
            'coprs': forms.CheckboxSelectMultiple(renderer=CheckboxSelectMultipleTableRenderer),
        }


class ReposForm(forms.ModelForm):
    repos = forms.MultipleChoiceField(label=_('Enabled repos'), required=False,
                widget=forms.CheckboxSelectMultiple(renderer=CheckboxSelectMultipleTableRenderer))

    def __init__(self, *args, **kwargs):
        super(ReposForm, self).__init__(*args, **kwargs)
        self.current_repos = dict(
            ('{}/{}/{}'.format(repo.copr.username, repo.copr.name, repo.name), repo)
            for repo in self.instance.all_repos
        )
        self.available_repos = {}
        self.fields['repos'].choices = []
        for copr in self.instance.all_coprs:
            label   = '{} / {}'.format(copr.username, copr.name)
            choices = []
            for name, url in sorted(copr.yum_repos.items()):
                slug = '{}/{}'.format(copr.slug, name)
                if slug in self.current_repos:
                    repo = self.current_repos[slug]
                else:
                    repo = Repo(
                        slug     = '{}/{}'.format(self.instance.slug, name),
                        scl      = self.instance,
                        copr     = copr,
                        name     = name,
                        copr_url = url,
                    )
                choices.append((
                    slug,
                    mark_safe('<img src="{}" width="32" height="32" alt=""/> {} {} {}'.format(
                        repo.get_icon_url(), repo.distro.title(), repo.version, repo.arch
                    )),
                ))
                self.available_repos[slug] = repo
            self.fields['repos'].choices.append((label, choices))
        self.initial['repos'] = self.current_repos.keys()

    def clean_copr_username(self):
        if self.fields['copr_username'].required and not self.coprnames:
            raise forms.ValidationError(_('No SCL project found for this Copr user.'))
        return self.cleaned_data['copr_username']

    def clean_copr_name(self):
        if self.fields['copr_username'].required and self.coprnames \
            and self.cleaned_data['copr_name'] not in self.coprnames:
            raise forms.ValidationError(_('This field is mandatory.'))
        return self.cleaned_data['copr_name']

    def clean_repos(self):
        repos = {}
        for slug in self.cleaned_data['repos']:
            copr_slug, name = slug.rsplit('/',1)
            if name in repos:
                raise forms.ValidationError(_('There may not be two repositories with the same name attached to one SCL.'))
            repos[name] = self.available_repos[slug]
        self.cleaned_data['repos'] = repos.values()
        return self.cleaned_data['repos']

    def save(self, commit=True):
        ids             = []
        download_count  = 0
        # save attached repos
        for repo in self.cleaned_data['repos']:
            if not repo.id:
                os.makedirs(repo.get_repo_dir())
                try:
                    os.unlink(repo.get_repo_symlink())
                except FileNotFoundError:
                    pass
                os.symlink(repo.repo_id, repo.get_repo_symlink())
                repo.save()
            ids.append(repo.id)
            download_count += repo.download_count
        # delete unattached repos
        for repo in self.instance.repos.exclude(id__in=ids):
            repo.delete()
        # drop repos cache
        del(self.instance.all_repos)
        # add auto tags
        self.instance.add_auto_tags()
        # update download count
        self.instance.download_count = download_count
        return super(ReposForm, self).save(commit)

    class Meta:
        model = SoftwareCollection
        fields = ['repos']


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
                        'placeholder': 'Search collections'}))
    search_desc = forms.BooleanField(required=False, label='search description')
    approved    = forms.BooleanField(required=False,
                    help_text='Display only collections, which have passed a review.',
                    widget=forms.CheckboxInput(attrs={'class': ''}))
    per_page    = forms.ChoiceField(required=False, label='Per page',
                    initial=PER_PAGE_CHOICES[0][0],
                    choices=PER_PAGE_CHOICES,
                    widget=forms.Select(attrs={'class': 'form-control input-sm'}))
    order_by    = forms.ChoiceField(required=False, label='Order',
                    initial=ORDER_BY_CHOICES[0][0],
                    choices=ORDER_BY_CHOICES,
                    widget=forms.Select(attrs={'class': 'form-control input-sm'}))
    policy      = forms.ChoiceField(required=False, label='Policy',
                    choices=[('', 'All policies')] + POLICY_CHOICES_LABEL,
                    widget=forms.Select(attrs={'class': 'form-control input-sm'}),
                    help_text= "policy help text")
    repo        = forms.ChoiceField(required=False, label='Repository',
                    widget=forms.Select(attrs={'class': 'form-control input-sm'}))

    def __init__(self, *args, **kwargs):
        super(FilterForm, self).__init__(*args, **kwargs)
        self.fields['repo'].choices = [('', 'All repos')] + sorted([
            (r['name'], r['name'].capitalize().replace('-', ' ', 1).replace('-', ' - '))
            for r in Repo.objects.values('name').distinct()
        ])

