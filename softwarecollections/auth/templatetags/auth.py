from django import template

register = template.Library()


class AllowedNode(template.base.Node):

    def __init__(self, *perms, ifnodes=None, elsenodes=None, user=None, obj=None):
        self.perms     = perms
        self.ifnodes   = ifnodes
        self.elsenodes = elsenodes
        self.user      = user
        self.obj       = obj

    def __repr__(self):
        return "<AllowedNode>"

    #def __iter__(self):
    #    for nodelist in self.ifnodes, self.elsenodes:
    #        for node in nodelist:
    #            yield node

    #@property
    #def nodelist(self):
    #    return NodeList(node for _, nodelist in self.conditions_nodelists for node in nodelist)

    def render(self, context):
        user = self.user.resolve(context) \
            if self.user else context['request'].user
        obj  = self.obj.resolve(context) \
            if self.obj else None
        perms = list(map(lambda perm: perm.resolve(context) \
                        if isinstance(perm, template.Variable) else perm, self.perms))
        if user.has_perms(perms, obj=obj):
            return self.ifnodes.render(context)
        elif self.elsenodes:
            return self.elsenodes.render(context)
        else:
            return ''


@register.tag
def allowed(parser, token):
    """
    The ``{% has_perms %}`` tag evaluates user permissions, and if the result is "true"
    (the user has appropriate permissions), the contents of the block are output::

        {% allowed 'news.add' %}
            <a href="{% url 'news:add' %}">write</a>
        {% notallowed %}
            You are not allowed to write news.
        {% endallowed %}

    ``allowed`` also accepts user=user argument to check permissions of given user::
        
        {% allowed user=u 'news.add' %}
            User {{u.get_full_name()}} is allowed to write news.
        {% endallowed %}

    and obj=obj to check permissions regarding particular object::

        {% allowed 'delete' obj=o %}
            <a href="{{ o.get_delete_url }}">delete</a>
        {% endallowed %}
    """
    # {% allowed ... %}
    args   = []
    kwargs = {}
    for arg in token.split_contents()[1:]:
        if arg[0] == arg[-1] and arg[0] in '\'"':
            args.append(arg[1:-1])
        elif arg.startswith('user='):
            kwargs['user'] = template.Variable(arg[5:])
        elif arg.startswith('obj='):
            kwargs['obj']  = template.Variable(arg[4:])
        else:
            args.append(template.Variable(arg))
            
    kwargs['ifnodes'] = parser.parse(('notallowed', 'endallowed'))
    token = parser.next_token()

    # {% notallowed %} (optional)
    if token.contents == 'notallowed':
        kwargs['elsenodes'] = parser.parse(('endallowed',))
        token = parser.next_token()

    # {% endallowed %}
    assert token.contents == 'endallowed'

    return AllowedNode(*args, **kwargs)

