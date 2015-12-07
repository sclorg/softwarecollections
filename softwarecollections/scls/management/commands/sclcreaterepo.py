import logging
import os

from optparse import make_option

from django.core.management.base import CommandError

from multiprocessing import Pool, cpu_count

from softwarecollections.management.commands import LoggingBaseCommand
from softwarecollections.scls.models import Repo


logger = logging.getLogger(__name__)


def createrepo(args):
    repo, timeout = args

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
            help='Timeout in seconds for each run of createrepo',
        ),
    )

    args = '[ <repo_slug> ... ]'
    help = 'Rebuild metadata for all repos. ' \
           'Optionaly you may specify one or more slug of particular repo to be processed.'

    def handle(self, *args, **options):
        self.configure_logging(options['verbosity'])
        errors = 0
        if args:
            repos = []
            for slug in args:
                try:
                    repos.append(Repo.objects.get(slug=slug))
                except Exception as e:
                    logging.error(str(e))
                    errors += 1
        else:
            repos = Repo.objects.all()
        timeout = options['timeout'] and int(options['timeout'])
        with Pool(processes=int(options['max_procs'])) as pool:
            errors += sum(pool.map(
                createrepo,
                [(scl, timeout) for scl in repos],
            ))
            if errors > 0:
                raise CommandError('Failed to rebuild release RPMs: {} error(s)'.format(errors))

