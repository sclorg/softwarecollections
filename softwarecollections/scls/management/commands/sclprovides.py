import logging
import os

from optparse import make_option

from django.core.management.base import CommandError

from multiprocessing import Pool, cpu_count

from softwarecollections.management.commands import LoggingBaseCommand
from softwarecollections.scls.models import SoftwareCollection


logger = logging.getLogger(__name__)


def dump_provides(args):
    scl, timeout = args

    # scl.dump_provides()
    logger.info('Dumping provides for {}'.format(scl.slug))
    try:
        scl.dump_provides(timeout)
    except:
        logger.exception('Failed to dump provides for {}'.format(scl.slug))
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
    help = 'Dump provides for all collections. ' \
           'Optionaly you may specify one or more slug of particular SCLs to be dumped.'

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
                dump_provides,
                [(scl, timeout) for scl in scls],
            ))
            if errors > 0:
                raise CommandError('Failed to dump provides: {} error(s)'.format(errors))

