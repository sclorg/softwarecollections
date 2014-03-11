"""Featured truncate filters."""

from django import template
from django.utils.text import Truncator


register = template.Library()


class TruncateNode(template.base.Node):

    def __init__(self, value, num, mode, stop):
        self.value = value
        self.num   = num
        self.mode  = mode
        self.stop  = stop

    def __repr__(self):
        return "<TruncateNode>"

    def render(self, context):
        value = self.value.render(context)
        num   = int(self.num.resolve(context))
        if self.stop is not None:
            stop = self.stop.render(context)
        else:
            stop = None

        if self.mode == 'chars':
            return Truncator(value).chars(num, truncate=stop)
        elif self.mode == 'words':
            return Truncator(value).words(num, truncate=stop)
        else:
            return Truncator(value).words(num, truncate=stop, html=True)


@register.tag
def truncate(parser, token):
    """
    The ``{% truncate %}`` tag is featured replacement of ``truncatechars``,
    ``truncatewords`` and ``truncatewords_html`` built-in filters.
    It allows to use other template tags to compose the ``value``
    to be truncated and custom stop.

    Examples:

        {% truncate 200 chars %}
            {{ obj.description }}
        {% endtruncate %}

        {% truncate 40 words %}
            {{ obj.description }}
        {% endtruncate %}

        {% truncate 40 words_html %}
            {{ obj.description }}
        {% truncatestop %}
            ... <a href="{{ obj.get_absolute_url }}">see more</a>
        {% endtruncate %}

    """
    # {% truncate ... %}
    try:
        tag_name, num, mode = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError('truncate tag requires two arguments')
    num = template.Variable(num)
    if mode not in ['chars', 'words', 'words_html']:
        raise template.TemplateSyntaxError('truncate mode must be one of chars, words or words_html')

    value = parser.parse(('truncatestop', 'endtruncate'))
    token = parser.next_token()

    # {% truncatestop %} (optional)
    if token.contents == 'truncatestop':
        stop = parser.parse(('endtruncate',))
        token = parser.next_token()
    else:
        stop = None

    # {% endtruncate %}
    assert token.contents == 'endtruncate'

    return TruncateNode(value, num, mode, stop)

