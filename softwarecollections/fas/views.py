from django.contrib.auth import login, REDIRECT_FIELD_NAME
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.views.decorators.http import require_POST

from social.actions import do_auth, do_complete, do_disconnect

from django.core.urlresolvers import reverse
from social.apps.django_app.utils import load_strategy
from functools import wraps

def strategy(redirect_uri=None, load_strategy=load_strategy):
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            uri = redirect_uri
            if uri and not uri.startswith('/'):
                uri = reverse(redirect_uri)

            request.social_strategy = load_strategy(
                request=request, backend='openid',
                redirect_uri=uri, *args, **kwargs
            )
            request.social_strategy.backend.URL = 'id.fedoraproject.org'

            # backward compatibility in attribute name, only if not already
            # defined
            if not hasattr(request, 'strategy'):
                request.strategy = request.social_strategy
            return func(request, *args, **kwargs)
        return wrapper
    return decorator


@strategy('fas:complete')
def login(request):
    return do_auth(request.social_strategy, redirect_name=REDIRECT_FIELD_NAME)


@csrf_exempt
@strategy('fas:complete')
def complete(request, *args, **kwargs):
    """Authentication complete view, override this view if transaction
    management doesn't suit your needs."""
    return do_complete(request.social_strategy, _do_login, request.user,
                       redirect_name=REDIRECT_FIELD_NAME, *args, **kwargs)


#@require_POST
#@csrf_protect
@login_required
@strategy()
def logout(request, association_id=None):
    """Disconnects fas from current logged in user."""
    return do_disconnect(request.social_strategy, request.user, association_id,
                         redirect_name=REDIRECT_FIELD_NAME)


def _do_login(strategy, user):
    login(strategy.request, user)
    # user.social_user is the used UserSocialAuth instance defined in
    # authenticate process
    social_user = user.social_user
    if strategy.setting('SESSION_EXPIRATION', True):
        # Set session expiration date if present and not disabled
        # by setting. Use last social-auth instance for current
        # provider, users can associate several accounts with
        # a same provider.
        expiration = social_user.expiration_datetime()
        if expiration:
            try:
                strategy.request.session.set_expiry(
                    expiration.seconds + expiration.days * 86400
                )
            except OverflowError:
                # Handle django time zone overflow
                strategy.request.session.set_expiry(None)
