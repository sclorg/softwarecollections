import re
import tagging
from django.db import models
from django.db.models import Avg
from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from softwarecollections.copr import CoprProxy

User = get_user_model()


class SoftwareCollection(models.Model):
    slug            = models.SlugField(max_length=150, editable=False)
    username        = models.CharField(_('User'), max_length=100)
    name            = models.CharField(_('Project'), max_length=200)
    description     = models.TextField(_('Description'))
    instructions    = models.TextField(_('Instructions'))
    policy          = models.TextField(_('Policy'))
    score           = models.SmallIntegerField(null=True, editable=False)
    score_count     = models.IntegerField(default=0, editable=False)
    download_count  = models.IntegerField(default=0, editable=False)
    create_date     = models.DateTimeField(_('Creation date'), auto_now_add=True)
    last_sync_date  = models.DateTimeField(_('Last sync date'), null=True)
    approved        = models.BooleanField(_('Approved'), default=False)
    approval_req    = models.BooleanField(_('Requested approval'), default=False)
    auto_sync       = models.BooleanField(_('Auto sync'), default=True)
    need_sync       = models.BooleanField(_('Needs sync with copr'), default=True)
    maintainer      = models.ForeignKey(User, verbose_name=_('Maintainer'),
                        related_name='maintained_softwarecollection_set')
    collaborators   = models.ManyToManyField(User,
                        verbose_name=_('Collaborators'),
                        related_name='softwarecollection_set', blank=True)

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

    def sync_copr_repos(self):
        repos = self.copr.yum_repos
        for repo in self.repos.all():
            if repo.name not in repos:
                # delete old repos
                repo.delete()
            else:
                # update existing repos
                repo.copr_url = repos.pop(repo.name)
                repo.save()
        for name in repos:
            # save new repos
            Repo(scl=self, name=name, copr_url=repos[name]).save()

    @property
    def title(self):
        return ' / '.join([self.username, self.name])

    def has_perm(self, user, perm):
        if perm in ['edit', 'delete']:
            return user.id == self.maintainer_id \
                or self in user.softwarecollection_set.all()
        elif perm == 'rate':
            return user.id != self.maintainer_id \
                or self not in user.softwarecollection_set.all()
        else:
            return False

    def save(self, *args, **kwargs):
        # ensure slug is correct
        self.slug = '/'.join((self.username, self.name))
        super(SoftwareCollection, self).save(*args, **kwargs)
        # ensure maintainer is collaborator
        self.collaborators.add(self.maintainer)

    class Meta:
        # in fact, since slug is made of those and slug is unique,
        # this is not necessarry, but as a side effect, it create index,
        # which may be useful
        unique_together = (('username', 'name'),)

tagging.register(SoftwareCollection)


class Repo(models.Model):
    scl             = models.ForeignKey(SoftwareCollection,
                        verbose_name=_('Maintainer'),
                        related_name='repos')
    name            = models.CharField(_('Name'), max_length=50)
    copr_url        = models.CharField(_('Copr URL'), max_length=200)
    download_count  = models.IntegerField(default=0, editable=False)
    create_date     = models.DateTimeField(_('Creation date'), auto_now_add=True)
    last_sync_date  = models.DateTimeField(_('Last sync date'), null=True)
    enabled         = models.BooleanField(_('Enabled'), default=True)
    auto_sync       = models.BooleanField(_('Auto sync'), default=True)
    need_sync       = models.BooleanField(_('Needs sync'), default=True)
    download_count  = models.IntegerField(default=0, editable=False)

    def __str__(self):
        return self.name

    class Meta:
        unique_together = (('scl', 'name'),)



class Score(models.Model):
    scl  = models.ForeignKey(SoftwareCollection, related_name='scores')
    user = models.ForeignKey(User)
    score = models.SmallIntegerField(choices=((n, n) for n in range(1,6)))

    # store average score on each change
    def save(self, *args, **kwargs):
        super(Score, self).save(*args, **kwargs)
        self.scl.score = self.scl.scores.aggregate(Avg('score'))['score__avg']
        self.scl.score_count = self.scl.scores.count()
        self.scl.save()

    # de
    def delete(self, *args, **kwargs):
        super(Score, self).delete(*args, **kwargs)
        self.scl.score = self.scl.scores.aggregate(Avg('score'))['score__avg']
        self.scl.score_count = self.scl.scores.count()
        self.scl.save()

    class Meta:
        unique_together = (('scl', 'user'),)

