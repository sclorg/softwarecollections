from django.db import models
from tagging.fields import TagField
from django.utils.translation import ugettext_lazy as _

class SoftwareCollection(models.Model):
    name        = models.CharField(_('Name'), max_length=200)
    version     = models.CharField(_('Version'), max_length=10)
    summary     = models.CharField(_('Summary'), max_length=200)
    description = models.TextField(_('Description'))
    tags        = TagField(_('Tags'))
