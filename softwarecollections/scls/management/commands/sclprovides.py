import logging
import os

from optparse import make_option

from django.core.management.base import BaseCommand, CommandError

from multiprocessing import Pool, cpu_count

from softwarecollections.scls.models import SoftwareCollection


logger = logging.getLogger(__name__)


def dump_provides(args):
    scl, timeout = args

    # scl.sync()
    logger.info('Searching relations {}'.format(scl.slug))
    exit_code = scl.dump_provides(timeout)
    if exit_code != 0:
        logger.error('Failed to search relations {}'.format(scl.slug))

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

    help = 'Dump provides for all collections'

    def handle(self, *args, **options):
        timeout = options['timeout'] and int(options['timeout'])
        with Pool(processes=int(options['max_procs'])) as pool:
            exit_code = sum(pool.map(
                dump_provides,
                [(scl, timeout) for scl in SoftwareCollection.objects.all()],
            ))
            if exit_code != 0:
                raise CommandError(exit_code)

