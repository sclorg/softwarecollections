import re
from django.core.validators import RegexValidator
from django.utils.translation import ugettext_lazy as _

name_re = re.compile(r'^[a-zA-Z0-9]([-a-zA-Z0-9_.]*[a-zA-Z0-9])?$')
name_re = re.compile(r'^[a-zA-Z0-9]+$')
validate_name = RegexValidator(name_re, _("Enter a valid name consisting of letters, numbers, underscores, hyphens or dots."), 'invalid')

