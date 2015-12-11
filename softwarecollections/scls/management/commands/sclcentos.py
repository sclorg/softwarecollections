import logging
import os

from optparse import make_option

from django.core.management.base import CommandError

from multiprocessing import Pool, cpu_count

from softwarecollections.management.commands import LoggingBaseCommand
from softwarecollections.scls.models import CentOSRepo


logger = logging.getLogger(__name__)


def centos_sync(args):
    repo, timeout = args
    logger.info('Syncing {}'.format(repo))
    try:
        repo.sync(timeout)
    except Exception as e:
        logger.error('Failed to sync {}: {}'.format(repo, e))
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
            help='Timeout in seconds for each step of centos (repocentos, rpmbuild, createrepo, dump_provides)',
        ),
    )

    help = 'Refresh CentOS repo information.'

    def handle(self, *args, **options):
        self.configure_logging(options['verbosity'])
        timeout = options['timeout'] and int(options['timeout'])
        with Pool(processes=int(options['max_procs'])) as pool:
            errors = sum(pool.map(
                centos_sync,
                [(repo, timeout) for repo in CentOSRepo.objects.all()],
            ))
            if errors > 0:
                raise CommandError('Failed to sync CentOS repos: {} error(s)'.format(errors))

