import re
from django.db import models
from django.db.models import Avg
import tagging
from tagging.models import Tag
from django.utils.translation import ugettext_lazy as _
from django.core.validators import RegexValidator
from django.core.urlresolvers import reverse
from django.contrib.auth import get_user_model

from softwarecollections.copr import CoprProxy

User = get_user_model()


UPDATE_FREQ_CHOICES = (
    ('OS', _('one shot')),
    ('RU', _('random updates, just make it work')),
    ('SU', _('security updates')),
)
UPDATE_FREQ = dict(UPDATE_FREQ_CHOICES)


REBASE_POLICY_CHOICES = (
    ('BP', _('backport bugfixes (stable, enterprise collections)')),
    ('RB', _('rebase')),
)
REBASE_POLICY = dict(REBASE_POLICY_CHOICES)


MATURITY_CHOICES = (
    ('D', _('development')),
    ('T', _('testing')),
    ('P', _('production')),
)
MATURITY = dict(MATURITY_CHOICES)


class SoftwareCollection(models.Model):
    slug            = models.SlugField(max_length=150, editable=False)
    username        = models.CharField(_('User'), max_length=100)
    name            = models.CharField(_('Project'), max_length=200)
    description     = models.TextField(_('Description'),  blank=True, editable=False)
    instructions    = models.TextField(_('Instructions'), blank=True, editable=False)
    update_freq     = models.CharField(_('Update frequency'), max_length=2,
                        choices=UPDATE_FREQ_CHOICES)
    rebase_policy   = models.CharField(_('Rebase policy'), max_length=2,
                        choices=REBASE_POLICY_CHOICES)
    maturity        = models.CharField(_('Maturity'), max_length=2,
                        choices=MATURITY_CHOICES)
    score           = models.SmallIntegerField(null=True, editable=False)
    maintainer      = models.ForeignKey(User, verbose_name=_('Maintainer'),
                        related_name='maintained_softwarecollection_set')
    collaborators   = models.ManyToManyField(User,
                        verbose_name=_('Collaborators'), blank=True)

    copr            = None

    def __init__(self, *args, **kwargs):
        if 'copr' in kwargs:
            self.copr = kwargs.pop('copr')
        elif 'username' in kwargs and 'name' in kwargs:
            self.copr = CoprProxy().copr(kwargs['username'], kwargs['name'])
        if self.copr:
            kwargs['slug']         = self.copr.slug
            kwargs['username']     = self.copr.username
            kwargs['name']         = self.copr.name
            kwargs['description']  = self.copr.description
            kwargs['instructions'] = self.copr.instructions
        super(SoftwareCollection, self).__init__(*args, **kwargs)

    def __str__(self):
        return self.slug

    def get_absolute_url(self):
        return reverse('scls:detail', kwargs={'slug': self.slug})

    def get_copr(self):
        self.copr = CoprProxy().copr(self.username, self.name)
        return self.copr

    @property
    def title(self):
        return ' / '.join([self.username, self.name])

    def save(self, *args, **kwargs):
        self.get_copr()
        self.slug         = self.copr.slug
        self.description  = self.copr.description
        self.instructions = self.copr.instructions
        super(SoftwareCollection, self).save(*args, **kwargs)

tagging.register(SoftwareCollection)


class Score(models.Model):
    scl  = models.ForeignKey(SoftwareCollection, related_name='scores')
    user = models.ForeignKey(User)
    score = models.SmallIntegerField()

    # store average score on each change
    def save(self, *args, **kwargs):
        super(Score, self).save(*args, **kwargs)
        self.scl.score = self.scl.scores.aggregate(Avg('score'))['score__avg']
        self.scl.save()

    class Meta:
        unique_together = (('scl', 'user'),)

