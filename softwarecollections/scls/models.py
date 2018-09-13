import markdown2
import os
import requests
import shutil
import time
from itertools import groupby
from datetime import datetime
from django.db import models
from django.db.models import Avg
from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.functional import cached_property
from django.utils.safestring import mark_safe
from django.utils.timezone import utc
from django.utils.translation import ugettext_lazy as _
from flock import Flock, LOCK_EX
from softwarecollections.copr import CoprProxy
from subprocess import call, check_call, check_output, CalledProcessError
from tagging.models import Tag
from tagging.registry import register
from tagging.utils import edit_string_for_tags

from .validators import validate_name


def check_call_log(args, **kwargs):
    try:
        kwargs['stderr'].write(' '.join(args) + '\n')
        kwargs['stderr'].flush()
        check_call(args, **kwargs)
        kwargs['stderr'].write('OK\n')
    except (OSError, CalledProcessError):
        kwargs['stderr'].write('FAILED\n')
        raise
    finally:
        kwargs['stderr'].flush()



ICON_NAMES = sorted(tuple(
    name[:-4]
    for name in os.listdir(os.path.join(os.path.dirname(__file__), 'static', 'scls', 'icons'))
    if name[-4:]=='.png' and name != 'empty.png'
))

ICON_NAME_CHOICES = ((name, name) for name in ICON_NAMES)

def get_icon_url(icon_name):
    return (icon_name in ICON_NAMES
       and '{}scls/icons/{}.png'.format(settings.STATIC_URL, icon_name)
        or '{}scls/icons/empty.png'.format(settings.STATIC_URL))


SPECFILE = os.path.join(os.path.dirname(__file__), 'scl-release.spec')
VERSION = '1'
RELEASE = '2'



# Tuple is needed to preserve the order of policies
POLICIES = ('DEV', 'Q-D', 'COM', 'PRO')

POLICY_TEXT = {
    'DEV':  '**Unpublished**: '
            'Collections not listed publicly. For projects in development '
            'stages before public release or projects for personal use. ',

    'Q-D':  '**Incubator**: '
            'Early-stage or experimental projects. May not be updated beyond '
            'the existing build. Not suitable for long-term use. ',

    'COM':  '**Community Project**: '
            'Maintained by upstream communities of developers. The software '
            'is cared for, but the developers make no commitments to update ' 'the repositories in a timely manner. ',

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
        return (self.detail['last_modified']
           and datetime.utcfromtimestamp(self.detail['last_modified']).replace(tzinfo=utc)
            or None)

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



class OtherRepo(models.Model):
    name            = models.CharField(_('Distribution name'), max_length=20)
    version         = models.CharField(_('Distribution version'), max_length=20, blank=True, default='')
    variant         = models.CharField(_('Variant'), max_length=20, blank=True, default='')
    arch            = models.CharField(_('Architecture'), max_length=20, blank=True, default='')
    icon            = models.CharField(_('Icon'), max_length=20, choices=ICON_NAME_CHOICES, blank=True, default='')
    url             = models.CharField(_('URL'), max_length=200, blank=True, default='')
    command         = models.TextField(_('Command'), blank=True, default='')
    last_modified   = models.DateTimeField(_('Last modified'), null=True, editable=False)
    last_synced     = models.DateTimeField(_('Last synced'), null=True, editable=False)

    class Meta:
        verbose_name        = 'Other repo'
        verbose_name_plural = 'Other repos'
        ordering            = ('name', 'version', 'variant', 'arch')
        unique_together     = (('name', 'version', 'variant', 'arch'),)

    def __str__(self):
        return '{name} {version} {variant} {arch}'.format(
            name    = self.name,
            version = self.version,
            variant = self.variant,
            arch    = self.arch,
        )

    def get_icon_url(self):
        return get_icon_url(self.icon)

    def sync(self, timeout=None):
        response = requests.head('{}/repodata/repomd.xml'.format(self.url))
        if response.status_code != 200:
            response.raise_for_status()
        self.last_modified = datetime.fromtimestamp(time.mktime(time.strptime(
            response.headers['Last-Modified'],
            '%a, %d %b %Y %H:%M:%S GMT'
        ))).replace(tzinfo=utc)
        self.last_synced = datetime.now().replace(tzinfo=utc)
        self.save()



class SoftwareCollection(models.Model):
    # automatic value (maintainer.username/name) used as unique key
    slug            = models.CharField(max_length=150, editable=False, db_index=True)
    # name is unique per maintainer
    name            = models.CharField(_('Name'), max_length=100, validators=[validate_name],
                        help_text=_('Name without spaces (It will be part of the url and RPM name.)'))
    coprs           = models.ManyToManyField(Copr, verbose_name=_('Copr projects'), blank=True)
    other_repos     = models.ManyToManyField(OtherRepo, verbose_name=_('Other repos'), blank=True)
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
    maintainer      = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_('Maintainer'),
                        related_name='maintained_softwarecollection_set')
    collaborators   = models.ManyToManyField(settings.AUTH_USER_MODEL,
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

    @cached_property
    def all_other_repos(self):
        return list(self.other_repos.all())

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
        for repo in self.all_other_repos:
            tags.update(['{}-{}'.format(repo.name, repo.version)])
        return list(tags)

    def get_default_instructions(self):
        return '''    # 1. Install the Software Collections tools:
    yum install scl-utils

    # 2. Download a package with repository for your system.
    #  (See the Yum Repositories section below. You can use `wget URL`.)

    # 3. Install the repo package:
    yum install {maintainer}-{name}-*.noarch.rpm

    # 4. Install the collection:
    yum install {name}

    # 5. Start using software collections:
    scl enable {name} bash
'''.format(name=self.name, maintainer=self.maintainer.get_username(), slug=self.slug)

    def add_auto_tags(self):
        for tag in self.get_auto_tags():
            Tag.objects.add_tag(self, tag)

    def tags_edit_string(self):
        return edit_string_for_tags(self.tags.exclude(name__in=self.get_auto_tags()))

    def sync(self, timeout=None):
        with self.lock:
            # create repos config
            repos_config = [
                '[main]\nreposdir=\ncachedir={cache_root}\nkeepcache=0\n'.format(cache_root=self.get_cache_root())
            ]
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
                        repos_config.append(
                            '[{name}]\nname={name}\nbaseurl={url}\ngpgcheck=0\n'.format(
                                name = repo.name,
                                url  = repo.copr_url,
                            )
                        )
                        all_repos.append(repo)
                        download_count += repo.download_count

            # save repos config
            with open(self.get_repos_config(), 'w') as f:
                f.write('\n'.join(repos_config))
                # despite expectations the file is empty
                # if I do not call explicitly flush
                f.flush()

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
                # TODO replace reposync with another tool,
                # which is capable of parallel run and preserves *-relese.rpm
                args = [
                    'reposync', '--source', '-c', self.get_repos_config(),
                    '-p', self.get_repos_root(),
                ]
                for repo in self.all_repos:
                    args += ['-r', repo.name]
                check_call_log(args, stdout=log, stderr=log, timeout=timeout)
            self.last_synced = datetime.now().replace(tzinfo=utc)

            self.check_repos_content(timeout)

    def check_repos_content(self, timeout):
        with self.lock:
            # check repos content and build repo RPMs
            for repo in self.repos.all():
                if not os.path.exists(repo.get_rpmfile_path()):
                    repo.rpmbuild(timeout)
                repo.createrepo(timeout)
                repo.last_synced = self.last_synced
                repo.has_content = len(repo.dump_provides(timeout)) > 0
                repo.save()
            self.has_content = (len(self.dump_provides(timeout)) + self.other_repos.count()) > 0
            self.save()

    def dump_provides(self, timeout=None):
        with self.lock:
            repos_root = self.get_repos_root()
            with open(os.path.join(repos_root, '.provides'), 'w+') as out:
                call(
                    "sort -u '{repos_root}'/*/.provides 2> /dev/null".format(
                        repos_root=repos_root
                    ),
                    shell=True, stdout=out, timeout=timeout
                )
                out.seek(0)
                return [line.rstrip() for line in out]

    def find_related(self, timeout=None):
        with self.lock:
            out = check_output(
                ("set -o pipefail; "
                "find '{repos_root}' -name '*.rpm' -exec rpm -qp --nosignature --requires '{{}}' \\; "
                "| sed 's/ .*//' | sort -u | while read req; do "
                "egrep -l \"^$req$\" '{all_repos_root}'/*/*/.provides || :; "
                "done | sed -r -e 's|^{all_repos_root}/||' -e 's|/.provides$||' | sort -u"
                .format(all_repos_root=settings.REPOS_ROOT, repos_root=self.get_repos_root())),
                shell=True, universal_newlines=True, timeout=timeout
            )
            related_slugs = [slug for slug in out.split() if slug != self.slug]
            self.requires = SoftwareCollection.objects.filter(slug__in=related_slugs)

    @cached_property
    def lock(self):
        try:
            return Flock(os.open(self.get_repos_root(), 0), LOCK_EX)
        except FileNotFoundError:
            os.makedirs(self.get_repos_root())
            return Flock(os.open(self.get_repos_root(), 0), LOCK_EX)

    def has_perm(self, user, perm):
        if perm in ['edit', 'delete']:
            return (user.id == self.maintainer_id
                or self in user.softwarecollection_set.all())
        elif perm == 'rate':
            return (user.id != self.maintainer_id
                or self not in user.softwarecollection_set.all())
        else:
            return False

    def save(self, *args, **kwargs):
        if self.auto_sync:
            self.need_sync = True
        if not self.instructions.strip():
            self.instructions = self.get_default_instructions()
        super(SoftwareCollection, self).save(*args, **kwargs)

register(SoftwareCollection)



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

    def get_cache_dir(self):
        return os.path.join(self.scl.get_cache_root(), self.name)

    def get_repo_dir(self):
        return os.path.join(self.scl.get_repos_root(), self.name)

    def get_repo_url(self):
        return os.path.join(self.scl.get_repos_url(), self.name)

    def get_rpmfile_path(self):
        return os.path.join(self.scl.get_repos_root(), self.name, 'noarch', self.rpmfile)

    def get_rpmfile_symlink_path(self):
        return os.path.join(self.scl.get_repos_root(), self.name, 'noarch', self.rpmfile_symlink)

    def get_rpmfile_url(self):
        return os.path.join(self.scl.get_repos_url(), self.name, 'noarch', self.rpmfile)

    def get_icon_url(self):
        return get_icon_url(self.distro)

    def get_download_url(self):
        return reverse('scls:download', kwargs={'slug': self.slug}) + self.rpmfile_symlink

    def get_oses_names_and_logos(self):
        if self.distro == 'epel':
            return [('RHEL {}'.format(self.version), get_icon_url('rhel')),
                    ('CentOS {}'.format(self.version), get_icon_url('centos'))]
        return [('{0} {1}'.format(self.distro, self.version), self.get_icon_url())]

    @cached_property
    def lock(self):
        try:
            return Flock(os.open(self.get_repo_dir(), 0), LOCK_EX)
        except FileNotFoundError:
            os.makedirs(self.get_repo_dir())
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
                '-D', 'scl_description {}'.format(self.scl.description.replace('%','%%')),
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
            tries = 5
            # createrepo_c sometimes fails with those two exit codes:
            #   - 6: At least one argument of function is bad or non complete
            #   - 11: Unknown/Unsupported compression type
            while True:
                try:
                    check_call_log([
                        'createrepo_c', '--database', '--update', '--skip-symlinks',
                        self.get_repo_dir()
                    ], stdout=log, stderr=log, timeout=timeout)
                    break
                except (OSError, CalledProcessError):
                    try:
                        shutil.rmtree(os.path.join(self.get_repo_dir(), ".repodata"))
                    except FileNotFoundError:
                        pass
                    tries -= 1
                    if not tries:
                        raise

    def dump_provides(self, timeout=None):
        with self.lock:
            repo_dir = self.get_repo_dir()
            with open(os.path.join(repo_dir, '.provides'), 'w+') as out:
                check_call(
                    ("set -o pipefail; "
                    "find '{repo_dir}' -name '*.rpm' -exec rpm -qp --nosignature --provides '{{}}' \\; "
                    "| sed 's/ .*//' | sort -u".format(repo_dir=repo_dir)),
                    shell=True, stdout=out, timeout=timeout
                )
                out.seek(0)
                return [line.rstrip() for line in out]



class Score(models.Model):
    scl  = models.ForeignKey(SoftwareCollection, related_name='scores')
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
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
