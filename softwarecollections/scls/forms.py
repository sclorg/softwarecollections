import markdown2
from django.forms import ModelForm, Select, RadioSelect, HiddenInput
from django.forms.forms import pretty_name
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from softwarecollections.copr import CoprProxy
from tagging.forms import TagField
from tagging.utils import edit_string_for_tags

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


class CreateForm(ModelForm):

    def __init__(self, request, **kwargs):
        self.request = request
        if 'copr_username' in request.REQUEST:
            copr_username = request.REQUEST['copr_username']
        else:
            copr_username = request.user.get_username()
        kwargs['initial'] = {'copr_username': copr_username}
        super(CreateForm, self).__init__(**kwargs)
        if copr_username:
            coprs = CoprProxy().coprs(copr_username)
        else:
            coprs = []
        copr_name_choices = tuple((copr.name, copr.slug) for copr in coprs)
        self.fields['copr_name'].widget.choices = copr_name_choices

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
        return obj

    class Meta:
        model = SoftwareCollection
        fields = ['copr_username', 'copr_name', 'policy']
        widgets = {
            'copr_username': HiddenInput(),
            'copr_name': Select(),
            'policy': RadioSelect(choices=POLICY_CHOICES),
        }


class UpdateForm(ModelForm):
    tags = TagField(max_length=200, required=False, help_text=_(
        'Enter space separated list of single word tags ' \
        'or comma separated list of tags containing spaces. ' \
        'Use doublequotes to enter name containing comma.'
    ))

    def __init__(self, *args, **kwargs):
        super(UpdateForm, self).__init__(*args, **kwargs)
        self.initial['tags'] = edit_string_for_tags(self.instance.tags)

    def save(self, commit=True):
        obj = super(UpdateForm, self).save(commit)
        obj.tags = self.cleaned_data['tags']
        return obj

    class Meta:
        model = SoftwareCollection
        fields = ['title', 'description', 'instructions', 'policy', 'auto_sync']


class RateForm(ModelForm):

    class Meta:
        model = Score
        fields = ['score']
        widgets = {
            'score': HiddenInput(),
        }

