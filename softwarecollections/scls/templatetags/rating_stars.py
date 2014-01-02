from django import template

register = template.Library()

@register.inclusion_tag("scls/stars.html", takes_context=True)
def rating_stars(context, state, scl, score=None):
    context.update({
        'active': state == 'active',
        'scl': scl,
        'score': scl.score if score is None else score,
    })
    return context

