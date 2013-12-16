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


class SoftwareCollection(models.Model):
    slug            = models.SlugField(max_length=150, editable=False)
    username        = models.CharField(_('User'), max_length=100)
    name            = models.CharField(_('Project'), max_length=200)
    description     = models.TextField(_('Description'),  blank=True)
    instructions    = models.TextField(_('Instructions'), blank=True)
    policy          = models.TextField(_('Policy'))
    score           = models.SmallIntegerField(null=True, editable=False)
    approved        = models.BooleanField(_('Approved'), default=False)
    need_sync       = models.BooleanField(_('Needs sync with copr'), default=True)
    maintainer      = models.ForeignKey(User, verbose_name=_('Maintainer'),
                        related_name='maintained_softwarecollection_set')
    collaborators   = models.ManyToManyField(User,
                        verbose_name=_('Collaborators'), related_name='softwarecollection_set', blank=True)

    _copr           = None

    def __init__(self, *args, **kwargs):
        if 'copr' in kwargs:
            self._copr = kwargs.pop('copr')
        elif 'username' in kwargs and 'name' in kwargs:
            self._copr = CoprProxy().copr(kwargs['username'], kwargs['name'])
        if self._copr:
            kwargs['slug']         = self._copr.slug
            kwargs['username']     = self._copr.username
            kwargs['name']         = self._copr.name
            kwargs['description']  = self._copr.description
            kwargs['instructions'] = self._copr.instructions
        super(SoftwareCollection, self).__init__(*args, **kwargs)

    def __str__(self):
        return self.slug

    def get_absolute_url(self):
        return reverse('scls:detail', kwargs={'slug': self.slug})

    def get_edit_url(self):
        return reverse('scls:edit', kwargs={'slug': self.slug})

    @property
    def copr(self):
        if not self._copr and self.username and self.name:
            self._copr = CoprProxy().copr(self.username, self.name)
        return self._copr

    @property
    def yum_repos(self):
        return self.copr.yum_repos

    @property
    def additional_repos(self):
        return self.copr.additional_repos

    @property
    def title(self):
        return ' / '.join([self.username, self.name])

    def has_perm(self, user, perm):
        if perm in ['edit', 'delete']:
            return user.id == self.maintainer_id \
                or self in user.softwarecollection_set.all()
        else:
            return False

    def save(self, *args, **kwargs):
        # refresh copr
        self._copr = None
        # update attributes
        self.slug         = self.copr.slug
        self.description  = self.copr.description
        self.instructions = self.copr.instructions
        super(SoftwareCollection, self).save(*args, **kwargs)

    class Meta:
        # in fact, since slug is made of those and slug is unique,
        # this is not necessarry, but as a side effect, it create index,
        # which may be useful
        unique_together = (('username', 'name'),)

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

