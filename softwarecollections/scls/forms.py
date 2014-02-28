import markdown2
from django import forms
from django.forms.forms import pretty_name
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from softwarecollections.copr import CoprProxy
from tagging.forms import TagField

from .models import SoftwareCollection, Score

POLICY_CHOICES = tuple((s.strip(), mark_safe(markdown2.markdown(s))) for s in [
    '''**Developing** - this is just for my testing purposes and it probably does not work yet.
And if this works I will put here update soon, which will most likely break it.
    ''',
    '''**Quick and Dirty** - I made this collection just for myself and few
of my colleagues. Do not expect bug-fixes, security patches or any kind of support.
    ''',
    '''**Just Works** - I plan to use this collection very often. You may
expect bug-fixes here. But only if my time allows me.
    ''',
    '''**Professional** - I will maintain this collections regularly. All fixes
will be done in timely manner. And security fixes will be back-ported as soon
as possible.
    ''',
])

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
        if 'copr_username' in request.REQUEST:
            copr_username = request.REQUEST['copr_username']
        else:
            copr_username = request.user.get_username()
        kwargs['initial'] = {'copr_username': copr_username}
        super(CreateForm, self).__init__(**kwargs)
        if copr_username:
            coprnames = CoprProxy().coprnames(copr_username)
        else:
            coprnames = []
        copr_name_choices = tuple((name, name) for name in coprnames)
        self.fields['copr_name'].widget.choices = copr_name_choices
        self.fields['copr_name'].widget.attrs['class'] = 'form-control'

    def save(self, commit=True):
        obj = super(CreateForm, self).save(False)
        obj.maintainer = self.request.user
        obj.title      = pretty_name(obj.copr_name)
        obj.name       = obj.copr_name
        while SoftwareCollection.objects.filter(
                maintainer=obj.maintainer,
                name=obj.name).count():
            obj.name += '_'
        obj.sync_copr_texts()
        if commit:
            obj.save()
            obj.sync_copr_repos()
            obj.add_auto_tags()
        return obj

    class Meta:
        model = SoftwareCollection
        fields = ['copr_username', 'copr_name', 'policy']
        widgets = {
            'copr_username': forms.HiddenInput(),
            'copr_name': forms.Select(),
            'policy': forms.RadioSelect(choices=POLICY_CHOICES),
        }

class UpdateForm(forms.ModelForm):
    tags = TagField(max_length=200, required=False, help_text=_(
        'Enter space separated list of single word tags ' \
        'or comma separated list of tags containing spaces. ' \
        'Use doublequotes to enter name containing comma.'
    ), widget=forms.TextInput(attrs={'class': 'form-control'}))

    def __init__(self, *args, **kwargs):
        super(UpdateForm, self).__init__(*args, **kwargs)
        self.initial['tags'] = self.instance.tags_edit_string()
        self.initial['policy'] = self.instance.policy

    def save(self, commit=True):
        obj = super(UpdateForm, self).save(commit)
        obj.tags = self.cleaned_data['tags']
        obj.add_auto_tags()
        return obj

    class Meta:
        model = SoftwareCollection
        fields = ['title', 'description', 'instructions', 'policy', 'auto_sync']
        widgets = {
                'title': forms.TextInput(attrs={'class': 'form-control'}),
                'description': forms.Textarea(attrs={'class': 'form-control', 'rows': '4'}),
                'instructions': forms.Textarea(attrs={'class': 'form-control', 'rows': '4'}),
                'policy': forms.RadioSelect(choices=POLICY_CHOICES),
                'auto_sync': forms.CheckboxInput(attrs={'class': 'form-control-static'}),
                }



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


