from django import template

register = template.Library()

@register.inclusion_tag("scls/stars.html", takes_context=True)
def rating_stars(context, state, score):
    context = {'active': state == 'active',
               'score': score,
               'scl': context['scl'],
               'request': context['request'],
               }
    return context

