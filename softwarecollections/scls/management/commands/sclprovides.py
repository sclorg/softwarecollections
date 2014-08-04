import logging
import os

from optparse import make_option

from django.core.management.base import BaseCommand, CommandError

from multiprocessing import Pool, cpu_count

from softwarecollections.scls.models import SoftwareCollection


logger = logging.getLogger(__name__)


def dump_provides(args):
    scl, timeout = args

    # scl.dump_provides()
    logger.info('Dumping provides for {}'.format(scl.slug))
    try:
        scl.dump_provides(timeout)
    except Exception as e:
        logger.error('Failed to dump provides for {}: {}'.format(scl.slug, e))
        return 1

    return 0


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

    args = '[ <scl_slug> ... ]'
    help = 'Dump provides for all collections. ' \
           'Optionaly you may specify one or more slug of particular SCLs to be dumped.'

    def handle(self, *args, **options):
        if args:
            scls = []
            for slug in args:
                scls.append(SoftwareCollection.objects.get(slug=slug))
        else:
            scls = SoftwareCollection.objects.all()
        timeout = options['timeout'] and int(options['timeout'])
        with Pool(processes=int(options['max_procs'])) as pool:
            exit_code = sum(pool.map(
                dump_provides,
                [(scl, timeout) for scl in scls],
            ))
            if exit_code != 0:
                raise CommandError('Failed to dump provides: {} error(s)'.format(exit_code))

