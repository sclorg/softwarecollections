"""
Definitions of template filters
"""
from softwarecollections.scls.models import POLICY_LABEL
from softwarecollections.scls.models import POLICY_TEXT
from django import template
from django.utils.safestring import mark_safe
register = template.Library()

@register.filter
def policy_name(value):
    name = POLICY_LABEL.get(value, "Unknown policy")
    description = POLICY_TEXT.get(value, "Unknown policy")
    result = "<span title=\"{0}\">{1}</span>".format(description, name)
    return mark_safe(result)
