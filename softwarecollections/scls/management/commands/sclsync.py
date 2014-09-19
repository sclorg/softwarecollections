import logging
import os

from optparse import make_option

from django.core.management.base import CommandError

from multiprocessing import Pool, cpu_count

from softwarecollections.management.commands import LoggingBaseCommand
from softwarecollections.scls.models import SoftwareCollection


logger = logging.getLogger(__name__)


def sync(args):
    scl, timeout = args
    exit_code = 0

    # scl.sync()
    logger.info('Syncing {}'.format(scl.slug))
    try:
        scl.sync(timeout)
        if not scl.auto_sync:
            scl.need_sync = False
            scl.save()
    except:
        logger.exception('Failed to sync {}'.format(scl.slug))
        exit_code += 1

    # scl.dump_provides()
    logger.info('Dumping provides for {}'.format(scl.slug))
    try:
        scl.dump_provides(timeout)
    except:
        logger.exception('Failed to dump provides for {}'.format(scl.slug))
        exit_code += 1

    return exit_code


class Command(LoggingBaseCommand):
    option_list = LoggingBaseCommand.option_list + (
        make_option(
            '-P', '--max-procs', action='store', dest='max_procs', default=cpu_count(),
            help='Run up to MAX_PROCS processes at a time (default {})'.format(cpu_count())
        ),
        make_option(
            '-t', '--timeout', action='store', dest='timeout', default=None,
            help='Timeout in seconds for each step of sync (reposync, rpmbuild, createrepo, dump_provides)',
        ),
    )

    args = '[ <scl_slug> ... ]'
    help = 'Sync all SCLs (marked with need_sync flag) with Copr repos. '\
           'Optionaly you may specify one or more slug of particular SCLs to be synced.'

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
            scls = SoftwareCollection.objects.filter(need_sync=True)
        timeout = options['timeout'] and int(options['timeout'])
        with Pool(processes=int(options['max_procs'])) as pool:
            errors += sum(pool.map(
                sync,
                [(scl, timeout) for scl in scls],
            ))
            if errors > 0:
                raise CommandError('Failed to sync SCLs: {} error(s)'.format(errors))

