from django.db import models
from django.db.models import Avg
from tagging.fields import TagField
from django.utils.translation import ugettext_lazy as _

from django.contrib.auth import get_user_model

UserModel = get_user_model()


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
    name            = models.CharField(_('Name'), max_length=200)
    version         = models.CharField(_('Version'), max_length=10)
    summary         = models.CharField(_('Summary'), max_length=200)
    description     = models.TextField(_('Description'), blank=True)
    update_freq     = models.CharField(_('Update frequency'), max_length=2,
                        choices=UPDATE_FREQ_CHOICES)
    rebase_policy   = models.CharField(_('Rebase policy'), max_length=2,
                        choices=REBASE_POLICY_CHOICES)
    maturity        = models.CharField(_('Maturity'), max_length=2,
                        choices=MATURITY_CHOICES)
    score           = models.SmallIntegerField(null=True, editable=False)
    maintainer      = models.ForeignKey(UserModel, verbose_name=_('Maintainer'),
                        related_name='maintained_softwarecollection_set')
    collaborators   = models.ManyToManyField(UserModel,
                        verbose_name=_('Collaborators'), blank=True)
    tags            = TagField(_('Tags'))

    def __str__(self):
        return self.name


class Score(models.Model):
    scl  = models.ForeignKey(SoftwareCollection, related_name='scores')
    user = models.ForeignKey(UserModel)
    score = models.SmallIntegerField()

    # store average score on each change
    def save(self, *args, **kwargs):
        super(Score, self).save(*args, **kwargs)
        self.scl.score = self.scl.scores.aggregate(Avg('score'))['score__avg']
        self.scl.save()

