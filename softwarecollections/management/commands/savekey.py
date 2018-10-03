"""Save secret key to SCL_SECRET_KEY_FILE if set"""

import logging
import os
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.management.utils import get_random_secret_key

ENVVAR = "SCL_SECRET_KEY_FILE"
COMMAND = Path(__file__).stem


class Command(BaseCommand):
    help = "Save secret key to {} if set".format(ENVVAR)
    log = logging.getLogger(__name__)

    def handle(self, *_args, **_options):
        candidate = os.getenv(ENVVAR, "")

        if not candidate:
            self.log.warning("%s not set, skipping", ENVVAR)
            return

        path = Path(candidate).resolve()
        if path.exists() and path.stat().st_size > 0:
            self.log.info("%s is not empty, keeping current content", path)
            return

        key = settings.SECRET_KEY or get_random_secret_key()
        path.write_text(key, encoding="utf-8")
        self.log.debug("Written %s into %s", key, path)
