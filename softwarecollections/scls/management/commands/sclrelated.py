import logging
import os

from optparse import make_option

from django.core.management.base import CommandError

from multiprocessing import Pool, cpu_count

from softwarecollections.management.commands import LoggingBaseCommand
from softwarecollections.scls.models import SoftwareCollection


logger = logging.getLogger(__name__)


def find_related(args):
    scl, timeout = args

    # scl.find_related()
    logger.info('Searching relations for {}'.format(scl.slug))
    try:
        scl.find_related(timeout)
    except Exception as e:
        logger.error('Failed to search relations for {}: {}'.format(scl.slug, e))
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

    args = '[ <scl_slug> ... ]'
    help = 'Find related collections for all collections. ' \
           'Optionaly you may specify one or more slug of particular SCLs to be precessed.'

    def handle(self, *args, **options):
        self.configure_logging(options['verbosity'])
        errors = 0
        if args:
            scls = []
            for slug in args:
                try:
                    scls.append(SoftwareCollection.objects.get(slug=slug))
                except Exception as e:
                    logging.error(str(e))
                    errors += 1
        else:
            scls = SoftwareCollection.objects.all()
        timeout = options['timeout'] and int(options['timeout'])
        with Pool(processes=int(options['max_procs'])) as pool:
            errors += sum(pool.map(
                find_related,
                [(scl, timeout) for scl in scls],
            ))
            if errors > 0:
                raise CommandError('Failed to find relations: {} error(s)'.format(errors))

