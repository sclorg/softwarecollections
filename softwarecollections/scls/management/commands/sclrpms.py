import logging
import os

from optparse import make_option

from django.core.management.base import CommandError

from multiprocessing import Pool, cpu_count

from softwarecollections.management.commands import LoggingBaseCommand
from softwarecollections.scls.models import Repo


logger = logging.getLogger(__name__)


def rpmbuild(args):
    repo, timeout = args

    # repo.rpmbuild()
    logger.info('Building RPM for {}'.format(repo.slug))
    try:
        repo.rpmbuild(timeout)
    except Exception as e:
        logger.error('Failed to build {}: {}'.format(repo.rpmname, e))
        return 1

    # repo.createrepo()
    logger.info('Creating repo {}'.format(repo.slug))
    try:
        repo.createrepo(timeout)
    except Exception as e:
        logger.error('Failed to create repo {}: {}'.format(repo.slug, e))
        return 1

    return 0


class Command(LoggingBaseCommand):
    option_list = LoggingBaseCommand.option_list + (
        make_option(
            '-P', '--max-procs', action='store', dest='max_procs', default=cpu_count(),
            help='Run up to MAX_PROCS processes at a time (default {})'.format(cpu_count())
        ),
        make_option(
            '-t', '--timeout', action='store', dest='timeout', default=None,
            help='Timeout in seconds for each step of sync (reposync, rpmbuild, createrepo)',
        ),
    )

    args = '[ <repo_slug> ... ]'
    help = 'Rebuild all release RPMs, ' \
           'Optionaly you may specify one or more slug of particular repo to be precessed.'

    def handle(self, *args, **options):
        self.configure_logging(options['verbosity'])
        if args:
            repos = []
            for slug in args:
                repos.append(Repo.objects.get(slug=slug))
        else:
            repos = Repo.objects.all()
        timeout = options['timeout'] and int(options['timeout'])
        with Pool(processes=int(options['max_procs'])) as pool:
            exit_code = sum(pool.map(
                rpmbuild,
                [(scl, timeout) for scl in repos],
            ))
            if exit_code != 0:
                raise CommandError('Failed to rebuild release RPMs: {} error(s)'.format(exit_code))

