from pkg_resources import get_distribution, parse_version

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.template.loader import render_to_string
from django.template.exceptions import TemplateDoesNotExist, TemplateSyntaxError

# Backward-compatible sekizai context
if get_distribution("django-sekizai").parsed_version >= parse_version("0.10.0"):
    from sekizai.context import sekizai
else:
    sekizai = dict


class Command(BaseCommand):
    help = "Generate static error pages."

    def handle(self, *_args, **_options):
        context = dict(sekizai(), ADMINS=settings.ADMINS)

        for error_page in "400.html", "403.html", "404.html", "500.html":
            try:
                path = settings.MEDIA_ROOT / error_page
                content = render_to_string(error_page, context=context)
                path.write_text(content, encoding="utf-8")

            except (IOError, TemplateDoesNotExist, TemplateSyntaxError) as err:
                message = "Cannot generate {error_page}: {err!s}".format_map(locals())
                raise CommandError from err
