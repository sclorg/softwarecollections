import fcntl
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
from django.utils.timezone import utc
from django.utils.translation import ugettext_lazy as _
from softwarecollections.copr import CoprProxy
from tagging.models import Tag
from tagging.utils import edit_string_for_tags

User = get_user_model()


SPECFILE = os.path.join(os.path.dirname(__file__), 'scl-release.spec')
VERSION = '1'
RELEASE = '1'

DISTRO_ICONS = ('fedora', 'epel')

class SclReposLocked(BlockingIOError):
    """ Repos temporarily unavailable """

class SclManager(models.Manager):
    def get_query_set(self):
        return super(SclManager, self).get_query_set().filter(deleted=False)

class SoftwareCollection(models.Model):
    objects = SclManager()

    everything = models.Manager()

    # automatic value (maintainer.username/name) used as unique key
    slug            = models.SlugField(max_length=150, editable=False)
    # local name is unique per local maintainer
    name            = models.SlugField(_('Name'), max_length=100, db_index=False)
    # copr_* are used to identify copr project
    copr_username   = models.CharField(_('Copr User'), max_length=100)
    copr_name       = models.CharField(_('Copr Project'), max_length=200)
    # other attributes are local
    title           = models.CharField(_('Title'), max_length=200)
    description     = models.TextField(_('Description'))
    instructions    = models.TextField(_('Instructions'))
    policy          = models.TextField(_('Policy'))
    score           = models.SmallIntegerField(null=True, editable=False)
    score_count     = models.IntegerField(default=0, editable=False)
    download_count  = models.IntegerField(default=0, editable=False)
    create_date     = models.DateTimeField(_('Creation date'), auto_now_add=True)
    last_modified   = models.DateTimeField(_('Last modified'), null=True, editable=False)
    approved        = models.BooleanField(_('Approved'), default=False)
    approval_req    = models.BooleanField(_('Requested approval'), default=False)
    auto_sync       = models.BooleanField(_('Auto sync'), default=True)
    need_sync       = models.BooleanField(_('Needs sync with copr'), default=True)
    deleted         = models.BooleanField(_('Marked for deletion'), default=False, editable=False)
    maintainer      = models.ForeignKey(User, verbose_name=_('Maintainer'),
                        related_name='maintained_softwarecollection_set')
    collaborators   = models.ManyToManyField(User,
                        verbose_name=_('Collaborators'),
                        related_name='softwarecollection_set', blank=True)

    class Meta:
        # in fact, since slug is made of those and slug is unique,
        # this is not necessarry, but as a side effect, it create index,
        # which may be useful
        unique_together = (
            ('maintainer', 'name'),)

    def __init__(self, *args, **kwargs):
        if 'copr' in kwargs:
            self._copr = kwargs.pop('copr')
            kwargs['copr_username'] = self._copr.username
            kwargs['copr_name']     = self._copr.name
        super(SoftwareCollection, self).__init__(*args, **kwargs)

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

    def get_enabled_repos(self):
        return self.repos.filter(enabled=True)

    def get_auto_tags(self):
        tags = set()
        for user in self.collaborators.all():
            tags.update([user.get_username()])
        for repo in self.repos.all():
            tags.update(repo.get_auto_tags())
        return list(tags)

    def add_auto_tags(self):
        for tag in self.get_auto_tags():
            Tag.objects.add_tag(self, tag)

    def tags_edit_string(self):
        return edit_string_for_tags(self.tags.exclude(name__in=self.get_auto_tags()))

    @property
    def copr(self):
        if not hasattr(self, '_copr'):
            if self.copr_username and self.copr_name:
                self._copr = CoprProxy().copr(self.copr_username, self.copr_name)
            else:
                return None
        return self._copr

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
        with self.repos_lock():
            download_count = 0
            for repo in self.get_enabled_repos():
                repo._sync()
                download_count += repo.download_count
            self.download_count = download_count
            self.last_modified  = self.copr.last_modified \
                and datetime.utcfromtimestamp(self.copr.last_modified).replace(tzinfo=utc) \
                 or None
            self.save()

    def repos_lock(self):
        # lock file name does not contain self.name,
        # for the case of scl renaming
        lock_file  = os.path.join(
            settings.REPOS_ROOT,
            self.maintainer.username,
            '{}.lock'.format(self.id)
        )
        try:
            lock = open(lock_file, 'w')
        except FileNotFoundError:
            os.makedirs(os.path.dirname(lock_file))
            lock = open(lock_file, 'w')
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as e:
            lock.close()
            raise SclReposLocked('Repos of {} temporarily unavailable'.format(self.slug))
        return lock

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
        self.slug = '/'.join((self.maintainer.username, self.name))

        #delete possible scl with the same slug that has not been really deleted yet
        zombie = SoftwareCollection.everything.filter(deleted=True, slug=self.slug)
        if zombie:
            zombie[0].delete()
        super(SoftwareCollection, self).save(*args, **kwargs)
        # ensure maintainer is collaborator
        self.collaborators.add(self.maintainer)

    def delete(self, *args, **kwargs):
        if os.path.isdir(scl.get_repos_root()):
            shutil.rmtree(scl.get_repos_root())
        super(SoftwareCollection, self).delete(*args, **kwargs)

tagging.register(SoftwareCollection)


class Repo(models.Model):
    # automatic value (scl.slug/name) used as unique key
    slug            = models.SlugField(max_length=150, editable=False)
    scl             = models.ForeignKey(SoftwareCollection, related_name='repos')
    name            = models.CharField(_('Name'), max_length=50)
    copr_url        = models.CharField(_('Copr URL'), max_length=200)
    download_count  = models.IntegerField(default=0, editable=False)
    create_date     = models.DateTimeField(_('Creation date'), auto_now_add=True)
    enabled         = models.BooleanField(_('Enabled'), default=True)
    auto_sync       = models.BooleanField(_('Auto sync'), default=True)
    need_sync       = models.BooleanField(_('Needs sync'), default=True)
    download_count  = models.IntegerField(default=0, editable=False)

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

    def _sync(self):
        """
        Run reposync and createrepo
        (should not be run directly, use scl.sync() to sync all repos at the same time)
        """

        fd, tempcfg = tempfile.mkstemp()
        try:
            cache_dir = os.path.join(
                settings.YUM_CACHE_ROOT,
                self.scl.copr_username,
                self.scl.copr_name,
                self.name
            )
            if not os.path.exists(cache_dir):
                os.makedirs(cache_dir)

            cfg = os.fdopen(fd, "w+")
            cfg.write("""[main]
reposdir=
cachedir={cache_dir}

[{name}]
name={name}
baseurl={url}
gpgcheck=0
""".format(cache_dir=cache_dir, name=self.name, url=self.copr_url))
            cfg.flush()
            cfg.close()

            definitions = ' '.join(['-D "{} {}"'.format(key, value) for key, value in {
                '_topdir':          settings.RPMBUILD_TOPDIR,
                '_rpmdir':          self.get_repo_root(),
                'dist':             self.distro_version,
                'scl_name':         self.scl.name,
                'scl_title':        self.scl.title,
                'scl_description':  self.scl.description,
                'repo_name':        self.name,
                'repo_version':     VERSION,
                'repo_release':     RELEASE,
                'repo_distro':      self.distro,
                'repo_arch':        self.arch,
                'repo_baseurl':     self.get_repo_url(),
            }.items()])
            command = "reposync -c {cfg} -p {destdir} -r {repoid} && " \
                      "( test -e {rpmfile_path} || rpmbuild -ba {definitions} {specfile}; ) && " \
                      "createrepo_c --database --update {destdir}/{repoid}" \
                      .format(cfg=tempcfg, destdir=self.scl.get_repos_root(), repoid=self.name,
                              definitions=definitions, rpmfile_path=self.get_rpmfile_path(), specfile=SPECFILE)

            subprocess.check_call(command, shell=True)
        finally:
            os.remove(tempcfg)

        self.save()

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

