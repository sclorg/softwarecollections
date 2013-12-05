import re
from django.db import models
from django.db.models import Avg
import tagging
from tagging.models import Tag
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _
from django.core.validators import RegexValidator
from django.core.urlresolvers import reverse
from django.contrib.auth import get_user_model

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


version_re = re.compile(r'^[-_.a-zA-Z0-9]+$')
validate_version = RegexValidator(version_re, _("Enter a valid 'version' consisting of numbers, dots, letters, underscores or hyphens."), 'invalid')


class SoftwareCollection(models.Model):
    slug            = models.SlugField(max_length=150, editable=False)
    name            = models.CharField(_('Name'), max_length=200)
    version         = models.CharField(_('Version'), max_length=10, validators=[validate_version])
    summary         = models.CharField(_('Summary'), max_length=200)
    description     = models.TextField(_('Description'), blank=True)
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

    def __str__(self):
        return self.slug

    def get_absolute_url(self):
        return reverse('scls:detail', kwargs={'slug': self.slug})

    def save(self, *args, **kwargs):
        self.slug = '%s/%s' % (slugify(self.name), self.version)
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

