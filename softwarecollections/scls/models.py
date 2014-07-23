import markdown2
import os
import shutil
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
from subprocess import call, check_call, check_output, CalledProcessError
from tagging.models import Tag
from tagging.utils import edit_string_for_tags

from .validators import validate_name

User = get_user_model()


SPECFILE = os.path.join(os.path.dirname(__file__), 'scl-release.spec')
VERSION = '1'
RELEASE = '2'

DISTRO_ICONS = ('fedora', 'epel')

# Tuple is needed to preserve the order of policies
POLICIES = ('DEV', 'Q-D', 'COM', 'PRO')

POLICY_TEXT = {
    'DEV':  '**Unpublished**: '
            'These SCLs are **not** listed publicly, so users browsing the '
            'SoftwareCollections.org index will not see these packages or be '
            'able to install them. This is for collections that are currently '
            'in development prior to release to the public, or for packages '
            'that are for your personal use.',
    'Q-D':  '**Incubator**: '
            'This software will be publicly listed, but users will be warned '
            "they are potentially unstable and there's no assurance of any "
            'effort to update the repository beyond the existing build. These '
            'repositories may be suitable for trying software that is not '
            'natively available for your system, but are considered not '
            'suitable for long-term use - and certainly not for production deployments.',
    'COM':  '**Community Repositories**: '
            'These repositories are cared for, possibly by upstream communities '
            'developing the software, but these are best-effort repositories '
            'that should not be depended on for production deployments. They '
            'are updated with bug fixes and security fixes, but the repository '
            'owner is not making any statement about doing so in a timely manner.',
    'PRO':  '**Professional**: '
            'These repositories are being developed to be used in production '
            'deployments. The individual or organization that maintains this '
            'repository is planning to issue updates, bug fixes, and security '
            'updates in a timely fashion.',

}


POLICY_LABEL = {
    'DEV': 'Unpublished',
    'Q-D': 'Incubator',
    'COM': 'Community Repositories',
    'PRO': 'Professional',
}

POLICY_CHOICES_TEXT = [(key, mark_safe(markdown2.markdown(POLICY_TEXT[key]))) for key in POLICIES]
POLICY_CHOICES_LABEL = [(key, POLICY_LABEL[key]) for key in POLICIES]

class SoftwareCollection(models.Model):
    # automatic value (maintainer.username/name) used as unique key
    slug            = models.CharField(max_length=150, editable=False, db_index=True)
    # local name is unique per local maintainer
    name            = models.CharField(_('Name'), max_length=100, validators=[validate_name],
                        help_text=_('Name without spaces (It will be part of the url and RPM name.)'))
    # copr_* are used to identify copr project
    copr_username   = models.CharField(_('Copr User'), max_length=100,
                        help_text=_('Username of Copr user (Note that the packages must be built in Copr.)'))
    copr_name       = models.CharField(_('Copr Project'), max_length=200,
                        help_text=_('Name of Copr Project to import packages from'))
    # other attributes are local
    issue_tracker   = models.URLField(_('Issue Tracker'), blank=True,
                        default='https://bugzilla.redhat.com/enter_bug.cgi?product=softwarecollections.org')
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
    last_synced     = models.DateTimeField(_('Last synced'), null=True, editable=False)
    approved        = models.BooleanField(_('Approved'), default=False)
    review_req      = models.BooleanField(_('Review requested'), default=False)
    auto_sync       = models.BooleanField(_('Auto sync'), default=False,
                        help_text=_('Enable periodic synchronization with related Copr project'))
    need_sync       = models.BooleanField(_('Needs sync with copr'), default=True)
    maintainer      = models.ForeignKey(User, verbose_name=_('Maintainer'),
                        related_name='maintained_softwarecollection_set')
    collaborators   = models.ManyToManyField(User,
                        verbose_name=_('Collaborators'),
                        related_name='softwarecollection_set', blank=True)
    requires        = models.ManyToManyField('self', symmetrical=False,
                        related_name='required_by', blank=True)

    class Meta:
        # in fact, since slug is made of those and slug is unique,
        # this is not necessarry, but as a side effect, it create index,
        # which may be useful
        unique_together = (('maintainer', 'name'),)

    def __str__(self):
        return self.slug

    def get_absolute_url(self):
        return reverse('scls:detail', kwargs={'slug': self.slug})

    def get_copr_url(self):
        return os.path.join(settings.COPR_COPRS_URL, self.copr_username, self.copr_name)

    # this is used in admin only
    def get_copr_tag(self):
        return '<a href="{url}" target="_blank">{username}/{name}</a>'.format(
            url      = self.get_copr_url(),
            username = self.copr_username,
            name     = self.copr_name,
        )
    get_copr_tag.short_description = _('Copr')
    get_copr_tag.allow_tags = True

    # this is used in admin only
    def get_title_tag(self):
        return '<a href="{url}" target="_blank">{title}</a>'.format(
            url   = self.get_absolute_url(),
            title = self.title,
        )
    get_title_tag.short_description = _('Title')
    get_title_tag.allow_tags = True

    def get_cache_root(self):
        return os.path.join(settings.YUM_CACHE_ROOT, self.slug)

    def get_repos_root(self):
        return os.path.join(settings.REPOS_ROOT, self.slug)

    def get_repos_url(self):
        return os.path.join(settings.REPOS_URL, self.slug)

    def get_repos_config(self):
        return os.path.join(settings.REPOS_ROOT, self.slug, 'copr-repos.conf')

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
        for repo in self.enabled_repos.all():
            tags.update([repo.distro_version])
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
        with self.lock:
            repos_config = open(self.get_repos_config(), 'w')
            repos_config.write(
                "[main]\nreposdir=\ncachedir={cache_root}\nkeepcache=0\n\n".format(cache_root=self.get_cache_root())
            )
            for name in repos:
                repos_config.write(
                    "[{name}]\nname={name}\nbaseurl={url}\ngpgcheck=0\n\n".format(
                        name=name, url=repos[name]
                    )
                )
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

    def reposync(self, timeout=None):
        # unfortunately reposync can not run parallel
        with Flock(os.open(settings.REPOS_ROOT, 0), LOCK_EX):
            with self.lock:
                log = open(os.path.join(self.get_repos_root(), 'reposync.log'), 'w')

                # workaround BZ 1079387
                call('rm -rf /var/tmp/yum-*', shell=True)

                # remove cache_root
                try:
                    shutil.rmtree(self.get_cache_root())
                except FileNotFoundError:
                    pass

                # run reposync
                args = [
                    'reposync', '--source', '-c', self.get_repos_config(),
                    '-p', self.get_repos_root(),
                ]
                for repo in self.repos.all():
                    args += ['-r', repo.name]
                log.write(' '.join(args) + '\n')
                log.flush()
                result = call(args, stdout=log, stderr=log, timeout=timeout)
                log.write('return code {0}'.format(result))
                return result

    def sync(self, timeout=None):
        self.sync_copr_repos()
        with self.lock:
            self.download_count = sum([repo.download_count for repo in self.repos.all()])
            self.reposync(timeout)
            self.last_modified = self.copr.last_modified \
                and datetime.utcfromtimestamp(self.copr.last_modified).replace(tzinfo=utc) \
                 or None
            self.last_synced = datetime.now().replace(tzinfo=utc)
            for repo in self.repos.all():
                if not os.path.exists(repo.get_rpmfile_path()):
                    repo.rpmbuild(timeout)
                repo.createrepo(timeout)
            self.save()

    def dump_provides(self, timeout=None):
        with self.lock:
            repos_root = self.get_repos_root()
            with open(os.path.join(repos_root, '.provides'), 'w') as out:
                check_call(
                    "set -o pipefail; " \
                    "find '{repos_root}' -name '*.rpm' -exec rpm -qp --provides '{{}}' \\; " \
                    "| sed 's/ .*//' | sort -u".format(repos_root=repos_root),
                    shell=True, stdout=out, timeout=timeout
                )

    def find_related(self, timeout=None):
        with self.lock:
            out = check_output(
                "set -o pipefail; " \
                "find '{repos_root}' -name '*.rpm' -exec rpm -qp --requires '{{}}' \\; " \
                "| sed 's/ .*//' | sort -u | while read req; do " \
                "egrep -l \"^$req$\" '{all_repos_root}'/*/*/.provides || :; " \
                "done | sed -r -e 's|^{all_repos_root}/||' -e 's|/.provides$||' | sort -u" \
                .format(all_repos_root=settings.REPOS_ROOT, repos_root=self.get_repos_root()),
                shell=True, universal_newlines=True, timeout=timeout
            )
            related_slugs = [slug for slug in out.split() if slug != self.slug]
            self.requires = SoftwareCollection.objects.filter(slug__in=related_slugs)

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
        # renamed directories will be deleted by command sclclean
        os.rename(
            self.get_repos_root(),
            os.path.join(
                settings.REPOS_ROOT,
                '.scl.{}.deleted'.format(self.id)
            )
        )
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
    def rpmname(self):
        return '-'.join([
            self.scl.maintainer.get_username(),
            self.scl.name,
            self.name,
        ])

    @property
    def rpmfile(self):
        return '-'.join([
            self.rpmname,
            VERSION,
            RELEASE,
        ]) + '.noarch.rpm'

    def get_cache_dir(self):
        return os.path.join(self.scl.get_cache_root(), self.name)

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
            defines = [
                '-D',         '_topdir {}'.format(settings.RPMBUILD_TOPDIR),
                '-D',         '_rpmdir {}'.format(self.get_repo_root()),
                '-D',            'dist {}'.format(self.distro_version),
                '-D',        'scl_name {}'.format(self.scl.name),
                '-D',       'scl_title {}'.format(self.scl.title),
                '-D', 'scl_description {}'.format(self.scl.description),
                '-D',       'repo_name {}'.format(self.name),
                '-D',        'pkg_name {}'.format(self.rpmname),
                '-D',     'pkg_version {}'.format(VERSION),
                '-D',     'pkg_release {}'.format(RELEASE),
                '-D',     'repo_distro {}'.format(self.distro),
                '-D',       'repo_arch {}'.format(self.arch),
                '-D',    'repo_baseurl {}'.format(self.get_repo_url()),
            ]
            if self.distro_version == 'epel-5':
                defines += [
                    '-D', '_source_filedigest_algorithm 1',
                    '-D', '_binary_filedigest_algorithm 1',
                    '-D', '_binary_payload w9.gzdio',
                ]
            check_call(
                ['rpmbuild', '-ba'] + defines + [ SPECFILE ],
                stdout=log, stderr=log, timeout=timeout
            )

    def createrepo(self, timeout=None):
        with self.lock:
            log = open(os.path.join(self.get_repo_root(), 'createrepo.log'), 'w')
            check_call([
                'createrepo_c', '--database', '--update', self.get_repo_root()
            ], stdout=log, stderr=log, timeout=timeout)

    def save(self, *args, **kwargs):
        # ensure slug is correct
        self.slug = '/'.join((self.scl.slug, self.name))
        super(Repo, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # rename of repo directory is faster than deleting
        # renamed directories will be deleted by command sclclean
        try:
            os.rename(
                self.get_repo_root(),
                os.path.join(
                    settings.REPOS_ROOT,
                    '.repo.{}.deleted'.format(self.id)
                )
            )
        except FileNotFoundError:
            pass
        # delete repo in the database
        super(Repo, self).delete(*args, **kwargs)



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

