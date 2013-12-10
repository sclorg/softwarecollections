from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from django.contrib.auth import login as auth_login, REDIRECT_FIELD_NAME
from django.contrib.auth.views import logout as auth_views_logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.views.decorators.http import require_POST
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from django.shortcuts import render, redirect, resolve_url

from django.core.urlresolvers import reverse

from openid.extensions import sreg
from openid.consumer.consumer import \
    Consumer as _Consumer, SUCCESS, CANCEL, FAILURE, SETUP_NEEDED

User = get_user_model()

try:
    import cPickle as pickle
except ImportError:
    import pickle


FAS_ID_URL = getattr(settings, 'FAS_ID_URL', 'https://id.fedoraproject.org')


class PickledSession(dict):
    def __init__(self, request):
        super(PickledSession, self).__init__(request.session.setdefault('FAS', {}))
    def __getitem__(self, name):
        return pickle.loads(bytes(super(PickledSession, self).__getitem__(name), 'utf-8'))
    def __setitem__(self, name, value):
        super(PickledSession, self).__setitem__(name, str(pickle.dumps(value, 0), 'utf-8'))


class Consumer(_Consumer):

    def __init__(self, request):
        super(Consumer, self).__init__(PickledSession(request), None)
        self.request = request

    def get_url(self, complete_url):
        req = self.begin(FAS_ID_URL)
        req.addExtension(sreg.SRegRequest(
            required=['nickname'],
            optional=['fullname', 'email'],
        ))
        message = req.getMessage(
            realm     = self.request.build_absolute_uri('/'),
            return_to = self.request.build_absolute_uri(complete_url),
            immediate=False)
        return message.toURL(req.endpoint.server_url)

    def complete(self):
        response = super(Consumer, self).complete(
            self.request.GET,
            self.request.build_absolute_uri(self.request.get_full_path()))
        return response
