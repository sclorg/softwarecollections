from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login as auth_login, logout as auth_logout, authenticate, REDIRECT_FIELD_NAME
from django.core.urlresolvers import resolve
from django.http import HttpResponseRedirect
from django.shortcuts import resolve_url, redirect
from django.utils.translation import ugettext_lazy as _
from urllib.parse import urlsplit, parse_qs, urlencode, urlunsplit

from .consumer import Consumer, SUCCESS, CANCEL, FAILURE, SETUP_NEEDED


STATUS_MESSAGES = {
    SUCCESS:      _('Login successful.'),
    CANCEL:       _('Login canceled.'),
    FAILURE:      _('Login failed.'),
    SETUP_NEEDED: _('Login needs setup.'),
}


def redirect_next(request, field_name, settings_name):
    try:
        # get safe url from user input
        url = request.REQUEST[field_name]
        url = urlunsplit(('','')+urlsplit(url)[2:])
    except:
        url = resolve_url(getattr(settings, settings_name, '/'))
    return HttpResponseRedirect(url)


def login(request, redirect_field_name=REDIRECT_FIELD_NAME,
          complete_view='fas:complete'):
    complete_url = resolve_url(complete_view)
    if redirect_field_name in request.REQUEST:
        (scheme, netloc, path, query_string, fragment) = urlsplit(complete_url)
        fields = parse_qs(query_string)
        fields[redirect_field_name] = request.REQUEST[redirect_field_name]
        complete_url = urlunsplit(('', '', path, urlencode(fields), fragment))
    return redirect(Consumer(request).get_url(complete_url=complete_url))


def complete(request, redirect_field_name=REDIRECT_FIELD_NAME):
    response = Consumer(request).complete()
    message  = STATUS_MESSAGES[response.status]
    user     = authenticate(response=response)
    if user:
        auth_login(request, user)
        messages.success(request, message)
        return redirect_next(request, redirect_field_name, 'LOGIN_REDIRECT_URL')
    else:
        messages.error(request, message)
        return redirect_next(request, redirect_field_name, 'LOGIN_FAIL_REDIRECT_URL')


def logout(request, redirect_field_name=REDIRECT_FIELD_NAME):
    auth_logout(request)
    messages.success(request, _('Successfully logged out.'))
    return redirect_next(request, redirect_field_name, 'LOGOUT_REDIRECT_URL')

