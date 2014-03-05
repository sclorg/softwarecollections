import markdown2
import os
import shutil
import subprocess
import tagging
import tempfile
from datetime import datetime
from django.db import models
from django.db.models import Avg
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.utils.timezone import utc
from django.utils.translation import ugettext_lazy as _
from flock import Flock, LOCK_EX
from softwarecollections.copr import CoprProxy
from tagging.models import Tag
from tagging.utils import edit_string_for_tags

User = get_user_model()


SPECFILE = os.path.join(os.path.dirname(__file__), 'scl-release.spec')
VERSION = '1'
RELEASE = '1'

DISTRO_ICONS = ('fedora', 'epel')

# Tuple is needed to preserve the order of policies
POLICIES = ('DEV', 'Q-D', 'COM', 'PRO')

POLICY_TEXT = {
    'DEV':  '**Developing**: '
            'Not publicly listed, this is primarily for developers trying out '
            'SoftwareCollections.org to see if they want to publish software '
            'or just for their own packaging purposes.',
    'Q-D':  '**Quick and Dirty**: '
            'Software will be publicly listed, but users will be warned '
            'it is not considered stable. May be useful for some users, '
            'but no guarantees.',
    'COM':  '**Community Repositories**: '
            'These repositories are cared for, but these are best-effort '
            'repositories that should not be used in production.',
    'PRO':  '**Professional**: '
            'Being developed to be used in production. '
            'The individual or team that maintains this repository is planning '
            'to issue updates, bug fixes, and security updates as needed.',
}


POLICY_LABEL = {
    'DEV': 'Developing',
    'Q-D': 'Quick and Dirty',
    'COM': 'Community Repositories',
    'PRO': 'Professional',
}

POLICY_CHOICES_TEXT = [(key, mark_safe(markdown2.markdown(POLICY_TEXT[key]))) for key in POLICIES]
POLICY_CHOICES_LABEL = [(key, POLICY_LABEL[key]) for key in POLICIES]

class SoftwareCollection(models.Model):
    # automatic value (maintainer.username/name) used as unique key
    slug            = models.SlugField(max_length=150, editable=False)
    # local name is unique per local maintainer
    name            = models.SlugField(_('Name'), max_length=100, db_index=False,
                        help_text=_('Name without spaces (It will be part of the url and rpm name.)'))
    # copr_* are used to identify copr project
    copr_username   = models.CharField(_('Copr User'), max_length=100,
                        help_text=_('Username of Copr user (Note that the packages must be built in Copr.)'))
    copr_name       = models.CharField(_('Copr Project'), max_length=200,
                        help_text=_('Name of Copr Project to import packages from'))
    # other attributes are local
    title           = models.CharField(_('Title'), max_length=200)
    description     = models.TextField(_('Description'))
    instructions    = models.TextField(_('Instructions'))
    policy          = models.CharField(_('Policy'), max_length=3, null=False,
                        choices=POLICY_CHOICES_TEXT, default='DEV')
    score           = models.SmallIntegerField(null=True, editable=False)
    score_count     = models.IntegerField(default=0, editable=False)
    download_count  = models.IntegerField(default=0, editable=False)
    create_date     = models.DateTimeField(_('Creation date'), auto_now_add=True)
    last_modified   = models.DateTimeField(_('Last modified'), null=True, editable=False)
    approved        = models.BooleanField(_('Approved'), default=False)
    approval_req    = models.BooleanField(_('Requested approval'), default=False)
    auto_sync       = models.BooleanField(_('Auto sync'), default=False)
    need_sync       = models.BooleanField(_('Needs sync with copr'), default=False)
    maintainer      = models.ForeignKey(User, verbose_name=_('Maintainer'),
                        related_name='maintained_softwarecollection_set')
    collaborators   = models.ManyToManyField(User,
                        verbose_name=_('Collaborators'),
                        related_name='softwarecollection_set', blank=True)

    class Meta:
        # in fact, since slug is made of those and slug is unique,
        # this is not necessarry, but as a side effect, it create index,
        # which may be useful
        unique_together = (('maintainer', 'name'),)

    def __str__(self):
        return self.slug

    def get_absolute_url(self):
        return reverse('scls:detail', kwargs={'slug': self.slug})

    def get_edit_url(self):
        return reverse('scls:edit', kwargs={'slug': self.slug})

    def get_repos_root(self):
        return os.path.join(settings.REPOS_ROOT, self.slug)

    def get_repos_url(self):
        return os.path.join(settings.REPOS_URL, self.slug)

    @property
    def policy_text(self):
        return POLICY_TEXT[self.policy]

    @property
    def enabled_repos(self):
        try:
            return self._enabled_repos
        except AttributeError:
            self._enabled_repos = self.repos.filter(enabled=True)
        return self._enabled_repos

    def get_auto_tags(self):
        tags = set()
        for user in self.collaborators.all():
            tags.update([user.get_username()])
        for repo in self.enabled_repos.all():
            tags.update(repo.get_auto_tags())
        return list(tags)

    def add_auto_tags(self):
        for tag in self.get_auto_tags():
            Tag.objects.add_tag(self, tag)

    def tags_edit_string(self):
        return edit_string_for_tags(self.tags.exclude(name__in=self.get_auto_tags()))

    @property
    def copr(self):
        try:
            return self._copr
        except AttributeError:
            if self.copr_username and self.copr_name:
                self._copr = CoprProxy().copr(self.copr_username, self.copr_name)
                return self._copr
            else:
                return None

    def sync_copr_texts(self):
        self.description = self.copr.description
        self.instructions = self.copr.instructions

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

    def sync(self):
        self.sync_copr_repos()
        with self.lock:
            download_count = 0
            for repo in self.enabled_repos.all():
                repo.sync()
                download_count += repo.download_count
            self.download_count = download_count
            self.last_modified  = self.copr.last_modified \
                and datetime.utcfromtimestamp(self.copr.last_modified).replace(tzinfo=utc) \
                 or None
            self.save()

    @property
    def lock(self):
        try:
            return self._lock
        except AttributeError:
            # do not try to create the repos root if it does not exist
            # it is always created before the collection is saved
            # so if it does not exist, it means that the collection was deleted
            self._lock = Flock(os.open(self.get_repos_root(), 0), LOCK_EX)
            return self._lock

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
        if self.auto_sync:
            self.need_sync = True
        super(SoftwareCollection, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # rename of repos root is faster than deleting
        # (name can not start with '.', therefore this is save)
        os.rename(self.get_repos_root(), os.path.join(
            settings.REPOS_ROOT,
            self.maintainer.username,
            '.{}.deleted'.format(self.id)
        ))
        # delete scl in the database
        super(SoftwareCollection, self).delete(*args, **kwargs)

tagging.register(SoftwareCollection)


class Repo(models.Model):
    # automatic value (scl.slug/name) used as unique key
    slug            = models.SlugField(max_length=150, editable=False)
    scl             = models.ForeignKey(SoftwareCollection, related_name='repos')
    name            = models.CharField(_('Name'), max_length=50)
    copr_url        = models.CharField(_('Copr URL'), max_length=200)
    download_count  = models.IntegerField(default=0, editable=False)
    enabled         = models.BooleanField(_('Enabled'), default=True)

    class Meta:
        # in fact, since slug is made of those and slug is unique,
        # this is not necessarry, but as a side effect, it create index,
        # which may be useful
        unique_together = (('scl', 'name'),)

    def __str__(self):
        return self.slug

    @property
    def distro(self):
        return self.name.rsplit('-', 2)[0]

    @property
    def version(self):
        return self.name.rsplit('-', 2)[1]

    @property
    def distro_version(self):
        return self.name.rsplit('-', 1)[0]

    @property
    def arch(self):
        return self.name.rsplit('-', 1)[1]

    @property
    def rpmfile(self):
        return '-'.join([
                self.scl.name,
                self.name,
                VERSION,
                RELEASE,
            ]) + '.noarch.rpm'

    def get_auto_tags(self):
        return [self.name, self.distro, self.distro_version, self.arch]

    def get_repo_root(self):
        return os.path.join(self.scl.get_repos_root(), self.name)

    def get_repo_url(self):
        return os.path.join(self.scl.get_repos_url(), self.name)

    def get_rpmfile_path(self):
        return os.path.join(self.scl.get_repos_root(), self.name, 'noarch', self.rpmfile)

    def get_rpmfile_url(self):
        return os.path.join(self.scl.get_repos_url(), self.name, 'noarch', self.rpmfile)

    def get_icon_url(self):
        return self.distro in DISTRO_ICONS \
           and '{}/scls/icons/{}.png'.format(settings.STATIC_URL, self.distro) \
            or '{}/scls/icons/empty.png'.format(settings.STATIC_URL)

    @property
    def lock(self):
        try:
            return self._lock
        except AttributeError:
            try:
                self._lock = Flock(os.open(self.get_repo_root(), 0), LOCK_EX)
            except FileNotFoundError:
                os.makedirs(self.get_repo_root())
                self._lock = Flock(os.open(self.get_repo_root(), 0), LOCK_EX)
            return self._lock

    def rpmbuild(self, timeout=None):
        with self.lock:
            log = open(os.path.join(self.get_repo_root(), 'rpmbuild.log'), 'w')
            return subprocess.call([
                'rpmbuild', '-ba',
                '-D',         '_topdir {}'.format(settings.RPMBUILD_TOPDIR),
                '-D',         '_rpmdir {}'.format(self.get_repo_root()),
                '-D',            'dist {}'.format(self.distro_version),
                '-D',        'scl_name {}'.format(self.scl.name),
                '-D',       'scl_title {}'.format(self.scl.title),
                '-D', 'scl_description {}'.format(self.scl.description),
                '-D',       'repo_name {}'.format(self.name),
                '-D',    'repo_version {}'.format(VERSION),
                '-D',    'repo_release {}'.format(RELEASE),
                '-D',     'repo_distro {}'.format(self.distro),
                '-D',       'repo_arch {}'.format(self.arch),
                '-D',    'repo_baseurl {}'.format(self.get_repo_url()),
                SPECFILE
            ], stdout=log, stderr=log, timeout=timeout)

    def reposync(self, timeout=None):
        with self.lock:
            log = open(os.path.join(self.get_repo_root(), 'reposync.log'), 'w')
            # create new cache dir
            cache_dir = os.path.join(
                settings.YUM_CACHE_ROOT,
                self.scl.copr_username,
                self.scl.copr_name,
                self.name
            )
            try:
                shutil.rmtree(cache_dir)
            except:
                pass
            finally:
                os.makedirs(cache_dir)

            # create config file
            cfg = os.path.join(cache_dir, 'repo.conf')
            with open(cfg, 'w') as f:
                f.write("[main]\nreposdir=\ncachedir={cache_dir}\n\n"
                        "[{name}]\nname={name}\nbaseurl={url}\ngpgcheck=0\n"
                        "".format(cache_dir=cache_dir, name=self.name, url=self.copr_url))

            # run reposync
            return subprocess.call([
                'reposync', '-c', cfg, '-p', self.scl.get_repos_root(), '-r', self.name
            ], stdout=log, stderr=log, timeout=timeout)

    def createrepo(self, timeout=None):
        with self.lock:
            log = open(os.path.join(self.get_repo_root(), 'createrepo.log'), 'w')
            return subprocess.call([
                'createrepo_c', '--database', '--update', self.get_repo_root()
            ], stdout=log, stderr=log, timeout=timeout)

    def sync(self):
        if os.path.exists(self.get_rpmfile_path()):
            return self.reposync() + self.createrepo()
        else:
            return self.rpmbuild() + self.reposync() + self.createrepo()

    def save(self, *args, **kwargs):
        # ensure slug is correct
        self.slug = '/'.join((self.scl.slug, self.name))
        super(Repo, self).save(*args, **kwargs)



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

    def delete(self, *args, **kwargs):
        super(Score, self).delete(*args, **kwargs)
        self.scl.score = self.scl.scores.aggregate(Avg('score'))['score__avg']
        self.scl.score_count = self.scl.scores.count()
        self.scl.save()

    class Meta:
        unique_together = (('scl', 'user'),)

