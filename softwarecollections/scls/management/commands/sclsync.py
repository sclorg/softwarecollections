import logging
import os

from optparse import make_option

from django.core.management.base import BaseCommand, CommandError

from multiprocessing import Pool, cpu_count

from softwarecollections.scls.models import SoftwareCollection


logger = logging.getLogger(__name__)


def sync(args):
    scl, timeout = args

    # scl.sync()
    logger.info('Syncing {}'.format(scl.slug))
    sync_exit_code = scl.sync(timeout)
    if sync_exit_code != 0:
        logger.error('Failed to sync {}'.format(scl.slug))

    # scl.provides()
    logger.info('Dumping provides {}'.format(scl.slug))
    provides_exit_code = scl.provides(timeout)
    if provides_exit_code != 0:
        logger.error('Failed to dump provides {}'.format(scl.slug))
    exit_code = sync_exit_code + provides_exit_code
    if not scl.auto_sync and exit_code != 0:
        scl.need_sync = False
        scl.save()
    return exit_code


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option(
            '-P', '--max-procs', action='store', dest='max_procs', default=cpu_count(),
            help='Run up to MAX_PROCS processes at a time (default {})'.format(cpu_count())
        ),
        make_option(
            '-t', '--timeout', action='store', dest='timeout', default=None,
            help='Timeout in seconds for each step of sync (reposync, rpmbuild, createrepo)',
        ),
    )

    help = 'Sync SCLs with copr repos'

    def handle(self, *args, **options):
        timeout = options['timeout'] and int(options['timeout'])
        with Pool(processes=int(options['max_procs'])) as pool:
            exit_code = sum(pool.map(
                sync,
                [(scl, timeout) for scl in SoftwareCollection.objects.filter(need_sync=True)],
            ))
            if exit_code != 0:
                raise CommandError(exit_code)

