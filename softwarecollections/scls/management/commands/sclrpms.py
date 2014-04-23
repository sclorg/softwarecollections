import logging
import os

from optparse import make_option

from django.core.management.base import BaseCommand, CommandError

from multiprocessing import Pool, cpu_count

from softwarecollections.scls.models import Repo


logger = logging.getLogger(__name__)


def rpmbuild(args):
    repo, timeout = args

    # repo.rpmbuild()
    logger.info('Building {}'.format(repo.rpmname))
    rpmbuild_exit_code = repo.rpmbuild()
    if rpmbuild_exit_code != 0:
        logger.error('Failed to build {}'.format(repo.rpmname))

    # repo.createrepo()
    logger.info('Creating repo {}'.format(repo.slug))
    createrepo_exit_code = repo.createrepo()
    if createrepo_exit_code != 0:
        logger.error('Failed to create repo {}'.format(repo.slug))

    return rpmbuild_exit_code + createrepo_exit_code


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

    help = 'Rebuild all release RPMs'

    def handle(self, *args, **options):
        timeout = options['timeout'] and int(options['timeout'])
        with Pool(processes=int(options['max_procs'])) as pool:
            exit_code = sum(pool.map(
                rpmbuild,
                [(scl, timeout) for scl in Repo.objects.all()],
            ))
            if exit_code != 0:
                raise CommandError(exit_code)

