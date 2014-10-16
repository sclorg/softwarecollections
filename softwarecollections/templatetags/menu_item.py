from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.simple_tag(takes_context = True)
def menu_item(context, path, name):
    path = path.strip("/")
    request = context["request"]
    # hack for software-collections-guide
    if path == 'en/docs/guide':
        active = "active" if request.path.startswith("/{path}/".format(path=path)) else ""
    else:
        active = "active" if request.path == "/{path}/".format(path=path) else ""
    item = "<li class='{active}' role='menuitem'>" \
           "    <a href='/{path}/'>{name}</a>" \
           "</li>".format(name=name, path=path, active=active)

    return mark_safe(item)
