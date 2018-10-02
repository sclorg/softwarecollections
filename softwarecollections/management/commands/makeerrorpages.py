from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.template.loader import render_to_string
from django.template.exceptions import TemplateDoesNotExist, TemplateSyntaxError
from sekizai.context_processors import sekizai


class Command(BaseCommand):
    help = "Generate static error pages."

    def handle(self, *_args, **_options):
        for error_page in "400.html", "403.html", "404.html", "500.html":
            try:
                path = settings.MEDIA_ROOT / error_page
                content = render_to_string(error_page, context=sekizai())
                path.write_text(content, encoding="utf-8")

            except (IOError, TemplateDoesNotExist, TemplateSyntaxError) as err:
                message = "Cannot generate {error_page}: {err!s}".format_map(locals())
                raise CommandError from err
