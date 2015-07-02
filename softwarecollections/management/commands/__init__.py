from django.conf import settings
from django.utils.module_loading import import_string
from django.core.management.base import BaseCommand

logging_levels  = {'3': 'DEBUG', '2': 'INFO', '1': 'WARNING', '0': 'ERROR'}
logging_formats = {
    '0': '%(module)s: %(message)s',
    '1': '%(levelname)s %(module)s: %(message)s',
    '2': '%(levelname)s %(module)s: %(message)s',
    '3': '%(asctime)s %(levelname)s %(module)s: %(message)s (pid: %(process)d/%(thread)d)',
}

class LoggingBaseCommand(BaseCommand):
    """
    Django is known to use Python’s builtin logging module to perform system logging
    (see https://docs.djangoproject.com/en/1.6/topics/logging/),
    however no Django's management command use it.
    There is --verbosity (-v) option in Django BaseCommand, but it does not handle it.
    Django's commands use command.stdout.write instead of logging.
    LoggingBaseCommand configures Python’s builtin logging acording to the verbosity option.
    """

    def configure_logging(self, verbosity):
        logging_config_func = import_string(settings.LOGGING_CONFIG)
        logging_config_func({
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'console': {
                    'format': logging_formats[verbosity]
                },
            },
            'handlers': {
                'console':{
                    'level': 'DEBUG',
                    'class': 'logging.StreamHandler',
                    'formatter': 'console',
                    'stream': self.stderr
                },
                'mail_admins': {
                    'level': 'ERROR',
                    'class': 'django.utils.log.AdminEmailHandler',
                },

            },
            'loggers': {
                '': {
                    'handlers': settings.DEBUG and ['console'] or ['console', 'mail_admins'],
                    'level': logging_levels[verbosity],
                    'propagate': True,
                }
            }
        })

