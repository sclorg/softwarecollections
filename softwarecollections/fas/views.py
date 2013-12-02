from django.conf import settings
from django.contrib.auth import login as auth_login, REDIRECT_FIELD_NAME
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.views.decorators.http import require_POST

from social.utils import module_member
from social.backends.utils import get_backend
from social.actions import do_auth, do_complete, do_disconnect

from django.core.urlresolvers import reverse
from social.apps.django_app.utils import BACKENDS, STORAGE, STRATEGY

from .backend import FasOpenId

Storage  = module_member(STORAGE)
Strategy = module_member(STRATEGY)


def login(request, *args, **kwargs):
    strategy = Strategy(FasOpenId, Storage, request, backends=BACKENDS,
                    redirect_uri=reverse('fas:complete'), *args, **kwargs)
    return do_auth(strategy, redirect_name=REDIRECT_FIELD_NAME)


@csrf_exempt
def complete(request, *args, **kwargs):
    strategy = Strategy(FasOpenId, Storage, request, backends=BACKENDS,
                    redirect_uri=reverse('fas:complete'), *args, **kwargs)
    return do_complete(strategy, _do_login, request.user,
                       redirect_name=REDIRECT_FIELD_NAME, *args, **kwargs)


@login_required
def logout(request, association_id=None):
    strategy = Strategy(FasOpenId, Storage, request, backends=BACKENDS,
                    redirect_uri=None)
    return do_disconnect(strategy, request.user, association_id,
                         redirect_name=REDIRECT_FIELD_NAME)


def _do_login(strategy, user):
    auth_login(strategy.request, user)
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
