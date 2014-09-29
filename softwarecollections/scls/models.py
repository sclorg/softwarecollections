import markdown2
import os
import shutil
import tagging
import tempfile
from itertools import groupby
from datetime import datetime
from django.db import models
from django.db.models import Avg
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.utils import timezone
from django.utils.functional import cached_property
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


def check_call_log(args, **kwargs):
    try:
        kwargs['stderr'].write(' '.join(args) + '\n')
        kwargs['stderr'].flush()
        check_call(args, **kwargs)
        kwargs['stderr'].write('OK\n')
    except:
        kwargs['stderr'].write('FAILED\n')
        raise
    finally:
        kwargs['stderr'].flush()



SPECFILE = os.path.join(os.path.dirname(__file__), 'scl-release.spec')
VERSION = '1'
RELEASE = '2'

DISTRO_ICONS = ('fedora', 'epel', 'rhel', 'centos')

# Tuple is needed to preserve the order of policies
POLICIES = ('DEV', 'Q-D', 'COM', 'PRO')

POLICY_TEXT = {
    'DEV':  '**Private project**: '
            'For personal or development use with no guarantee. '
            'Not listed publicly. '
            'Could be a good choice for projects in pre-release stage. ',

    'Q-D':  '**Experimental project**: '
            'An early-stage or experimental project. '
            'Comes with no warranty. '
            'Could be unstable - not for production use. ',

    'COM':  '**Community project**: '
            'Maintained by the upstream community of developers. '
            'Should work well and be updated for bug and security fixes. '
            'Still not recommended for use in production. ',

    'PRO':  '**Professional project**: '
            'Stable and secure release. '
            'Receives regular bug and security fixes. '
            'Ready for production deployments. ',
}

POLICY_LABEL = {
    'DEV': 'Private project',
    'Q-D': 'Experimental project',
    'COM': 'Community project',
    'PRO': 'Professional project',
}

POLICY_CHOICES_TEXT = [(key, mark_safe(markdown2.markdown(POLICY_TEXT[key]))) for key in POLICIES]
POLICY_CHOICES_LABEL = [(key, POLICY_LABEL[key]) for key in POLICIES]



class Copr(models.Model):
    username    = models.CharField(_('Copr User'), max_length=100,
                    help_text=_('Username of Copr user (Note that the packages must be built in Copr.)'))
    name        = models.CharField(_('Copr Project'), max_length=200,
                    help_text=_('Name of Copr Project to import packages from'))

    class Meta:
        unique_together = (('username', 'name'),)

    def get_url(self):
        return os.path.join(settings.COPR_COPRS_URL, self.username, self.name)

    @cached_property
    def detail(self):
        return CoprProxy().coprdetail(self.username, self.name)

    @property
    def additional_repos(self):
        return self.detail['additional_repos'].split(' ')

    @property
    def last_modified(self):
        return self.detail['last_modified'] \
           and datetime.utcfromtimestamp(self.detail['last_modified']).replace(tzinfo=utc) \
            or None

    @property
    def description(self):
        return self.detail['description']

    @property
    def instructions(self):
        return self.detail['instructions']

    @property
    def yum_repos(self):
        return self.detail['yum_repos']

    def __str__(self):
        return 'Copr(username={}, name={})'.format(self.username, self.name)

    @property
    def slug(self):
        return '/'.join([self.username, self.name])



class SoftwareCollection(models.Model):
    # automatic value (maintainer.username/name) used as unique key
    slug            = models.CharField(max_length=150, editable=False, db_index=True)
    # name is unique per maintainer
    name            = models.CharField(_('Name'), max_length=100, validators=[validate_name],
                        help_text=_('Name without spaces (It will be part of the url and RPM name.)'))
    coprs           = models.ManyToManyField(Copr, verbose_name=_('Copr projects'))
    upstream_url    = models.URLField(_('Project homepage'), blank=True)
    issue_tracker   = models.URLField(_('Issue Tracker'), blank=True,
                        default='https://bugzilla.redhat.com/enter_bug.cgi?product=softwarecollections.org')
    title           = models.CharField(_('Title'), max_length=200)
    description     = models.TextField(_('Description'))
    instructions    = models.TextField(_('Instructions'), blank=True,
                         help_text=_('Leave empty to use generic instructions'))
    policy          = models.CharField(_('Policy'), max_length=3, null=False,
                        choices=POLICY_CHOICES_TEXT, default='DEV')
    score           = models.SmallIntegerField(null=True, editable=False)
    score_count     = models.IntegerField(default=0, editable=False)
    download_count  = models.IntegerField(default=0, editable=False)
    create_date     = models.DateTimeField(_('Creation date'), auto_now_add=True)
    last_modified   = models.DateTimeField(_('Last modified'), null=True, editable=False)
    last_synced     = models.DateTimeField(_('Last synced'), null=True, editable=False)
    has_content     = models.BooleanField(_('Has content'), default=False)
    approved        = models.BooleanField(_('Approved'), default=False)
    review_req      = models.BooleanField(_('Review requested'), default=False)
    auto_sync       = models.BooleanField(_('Auto sync'), default=False,
                        help_text=_('Enable periodic synchronization with related Copr project'))
    need_sync       = models.BooleanField(_('Needs sync with coprs'), default=True)
    maintainer      = models.ForeignKey(User, verbose_name=_('Maintainer'),
                        related_name='maintained_softwarecollection_set')
    collaborators   = models.ManyToManyField(User,
                        verbose_name=_('Collaborators'),
                        related_name='softwarecollection_set', blank=True)
    requires        = models.ManyToManyField('self', symmetrical=False,
                        related_name='required_by', editable=False)

    class Meta:
        # in fact, since slug is made of those and slug is unique,
        # this is not necessarry, but as a side effect, it creates index,
        # which may be useful
        unique_together = (('maintainer', 'name'),)

    def __str__(self):
        return self.slug

    def get_absolute_url(self):
        return reverse('scls:detail', kwargs={'slug': self.slug})

    def get_copr_tags(self):
        return ', '.join([
            '<a href="{url}" target="_blank">{username}/{name}</a>'.format(
                url      = copr.get_url(),
                username = copr.username,
                name     = copr.name,
            ) for copr in self.all_coprs
        ])
    get_copr_tags.short_description = _('Coprs')
    get_copr_tags.allow_tags = True

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

    @cached_property
    def all_collaborators(self):
        return list(self.collaborators.all())

    @cached_property
    def all_coprs(self):
        return list(self.coprs.all())

    @cached_property
    def all_repos(self):
        return list(self.repos.all().order_by('name'))

    @property
    def all_repos_grouped(self):
        repo_groups = []
        for key, group in groupby(self.all_repos, lambda x: x.distro_version):
            repos = list(group)
            oses = repos[0].get_oses_names_and_logos()
            repo_groups.append((oses, repos))
        return repo_groups

    def get_auto_tags(self):
        tags = set()
        for repo in self.all_repos:
            tags.update([repo.distro_version])
        return list(tags)

    def get_default_instructions(self):
        return '''    # 1. Install the Software Collections tools:
    yum install scl-utils

    # 2. Install repo configuration for Your system (see section Yum Repositories bellow)
    yum install {maintainer}-{name}-*.noarch.rpm

    # 2. Install a collection
    yum install {name}

    # 3. Start using software collections
    scl enable {name}
'''.format(name=self.name, maintainer=self.maintainer.get_username(), slug=self.slug)

    def add_auto_tags(self):
        for tag in self.get_auto_tags():
            Tag.objects.add_tag(self, tag)

    def tags_edit_string(self):
        return edit_string_for_tags(self.tags.exclude(name__in=self.get_auto_tags()))

    def sync(self, timeout=None):
        with self.lock:
            # create repos_config
            with open(self.get_repos_config(), 'w') as repos_config:
                repos_config = open(self.get_repos_config(), 'w')
                repos_config.write(
                    '[main]\nreposdir=\ncachedir={cache_root}\nkeepcache=0\n\n'.format(cache_root=self.get_cache_root())
                )
                last_modified  = None
                download_count = 0
                all_repos      = []
                for copr in self.all_coprs:
                    if copr.last_modified:
                        if last_modified:
                            last_modified = max(last_modified, copr.last_modified)
                        else:
                            last_modified = copr.last_modified
                    for repo in self.repos.filter(copr=copr):
                        if repo.name not in copr.yum_repos:
                            # delete old repos
                            repo.delete()
                        else:
                            # update existing repos
                            repo.copr_url = copr.yum_repos[repo.name]
                            repo.save()
                            repos_config.write(
                                '[{name}]\nname={name}\nbaseurl={url}\ngpgcheck=0\n\n'.format(
                                    name = repo.repo_id,
                                    url  = repo.copr_url,
                                )
                            )
                            all_repos.append(repo)
                            download_count += repo.download_count
                # despite expectations the file is empty
                # if I do not call explicitly flush
                repos_config.flush()

            # scl.all_repos are expected to be sorted by name
            all_repos.sort(key=lambda repo: repo.name)

            # store newly computed values
            self.all_repos      = all_repos
            self.last_modified  = last_modified
            self.download_count = download_count

            # unfortunately reposync can not run parallel
            with Flock(os.open(settings.REPOS_ROOT, 0), LOCK_EX):
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
                for repo in self.all_repos:
                    args += ['-r', repo.repo_id]
                check_call_log(args, stdout=log, stderr=log, timeout=timeout)
            self.last_synced = datetime.now().replace(tzinfo=utc)

            # check repos content and build repo RPMs
            has_content = False
            for repo in self.all_repos:
                if not os.path.exists(repo.get_rpmfile_path()):
                    repo.rpmbuild(timeout)
                repo.createrepo(timeout)
                repo.last_synced = self.last_synced
                repo.has_content = list(filter(
                    lambda name: name.endswith('.rpm'),
                    os.listdir(repo.get_repo_dir())
                )) and True or False
                repo.save()
                has_content |= repo.has_content
            self.has_content = has_content
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

    @cached_property
    def lock(self):
        return Flock(os.open(self.get_repos_root(), 0), LOCK_EX)

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
        if not self.instructions.strip():
            self.instructions = self.get_default_instructions()
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
    copr            = models.ForeignKey(Copr, related_name='repos')
    name            = models.CharField(_('Name'), max_length=50)
    copr_url        = models.CharField(_('Copr URL'), max_length=200)
    download_count  = models.IntegerField(default=0, editable=False)
    last_synced     = models.DateTimeField(_('Last synced'), null=True, editable=False)
    has_content     = models.BooleanField(_('Has content'), default=False)

    class Meta:
        # in fact, since slug is made of those and slug is unique,
        # this is not necessarry, but as a side effect, it creates index,
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

    @property
    def rpmfile_symlink(self):
        return self.rpmname + '.noarch.rpm'

    @property
    def repo_id(self):
        try:
            return self._repo_id
        except AttributeError:
            self._repo_id= '-'.join([
                self.copr.username,
                self.copr.name,
                self.name
            ])
        return self._repo_id

    def get_cache_dir(self):
        return os.path.join(self.scl.get_cache_root(), self.name)

    def get_repo_dir(self):
        return os.path.join(self.scl.get_repos_root(), self.repo_id)

    def get_repo_symlink(self):
        return os.path.join(self.scl.get_repos_root(), self.name)

    def get_repo_url(self):
        return os.path.join(self.scl.get_repos_url(), self.name)

    def get_rpmfile_path(self):
        return os.path.join(self.scl.get_repos_root(), self.name, 'noarch', self.rpmfile)

    def get_rpmfile_symlink_path(self):
        return os.path.join(self.scl.get_repos_root(), self.name, 'noarch', self.rpmfile_symlink)

    def get_rpmfile_url(self):
        return os.path.join(self.scl.get_repos_url(), self.name, 'noarch', self.rpmfile)

    def get_icon_url(self, distro_name=None):
        if not distro_name:
            distro_name = self.distro
        return distro_name in DISTRO_ICONS \
           and '{}/scls/icons/{}.png'.format(settings.STATIC_URL, distro_name) \
            or '{}/scls/icons/empty.png'.format(settings.STATIC_URL)

    def get_oses_names_and_logos(self):
        if self.distro == 'epel':
            return [('RHEL {}'.format(self.version), self.get_icon_url('rhel')),
                    ('CentOS {}'.format(self.version), self.get_icon_url('centos'))]
        return [('{0} {1}'.format(self.distro, self.version), self.get_icon_url)]

    @cached_property
    def lock(self):
        return Flock(os.open(self.get_repo_dir(), 0), LOCK_EX)

    def rpmbuild(self, timeout=None):
        with self.lock:
            log = open(os.path.join(self.get_repo_dir(), 'rpmbuild.log'), 'w')
            defines = [
                '-D',         '_topdir {}'.format(settings.RPMBUILD_TOPDIR),
                '-D',         '_rpmdir {}'.format(self.get_repo_dir()),
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
            check_call_log(
                ['rpmbuild', '-ba'] + defines + [ SPECFILE ],
                stdout=log, stderr=log, timeout=timeout
            )
            try:
                os.unlink(self.get_rpmfile_symlink_path())
            except FileNotFoundError:
                pass
            os.symlink(self.rpmfile, self.get_rpmfile_symlink_path())

    def createrepo(self, timeout=None):
        with self.lock:
            log = open(os.path.join(self.get_repo_dir(), 'createrepo.log'), 'w')
            check_call_log([
                'createrepo_c', '--database', '--update', '--skip-symlinks',
                self.get_repo_dir()
            ], stdout=log, stderr=log, timeout=timeout)

    def delete(self, *args, **kwargs):
        # rename of repo directory is faster than deleting
        # renamed directories will be deleted by command sclclean
        try:
            os.rename(
                self.get_repo_dir(),
                os.path.join(
                    settings.REPOS_ROOT,
                    '.repo.{}.deleted'.format(self.id)
                )
            )
        except FileNotFoundError:
            pass
        try:
            os.unlink(self.get_repo_symlink())
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

