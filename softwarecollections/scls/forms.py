from django.forms import ModelForm, RadioSelect
from django.utils.translation import ugettext_lazy as _

from .models import SoftwareCollection

POLICY_CHOICES = tuple((s, s) for s in [
    '''quick and dirty
Lorem ipsum dolor sit amet, consectetur
adipisicing elit, sed do eiusmod tempor incididunt ut labore
et dolore magna aliqua. Ut enim ad minim veniam.''',
    '''stable
Lorem ipsum dolor sit amet, consectetur
adipisicing elit, sed do eiusmod tempor incididunt ut labore
et dolore magna aliqua. Ut enim ad minim veniam.
''',
])

class CreateForm(ModelForm):

    class Meta:
        model = SoftwareCollection
        fields = ['username', 'name', 'policy']
        widgets = {
            'policy': RadioSelect(choices=POLICY_CHOICES),
        }

