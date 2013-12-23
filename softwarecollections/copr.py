import requests
import json
import subprocess
import tempfile
import os

from django.conf import settings

COPR_API_URL = getattr(settings, 'COPR_API_URL', 'http://copr-fe.cloud.fedoraproject.org/api')


class CoprException(Exception):
    pass


class Copr(object):
    _fields = [
        'username',
        'name',
        'description',
        'instructions',
        'yum_repos',
        'additional_repos',
    ]

    def __init__(self, **kwargs):
        for field in kwargs:
            setattr(self, field, kwargs[field])

    def __str__(self):
        return 'copr://{}/{}'.format(self.username, self.name)

    def __repr__(self):
        return 'Copr({})'.format(', '.join(['{} = {}'.format(field, repr(getattr(self, field))) for field in self._fields]))

    @property
    def slug(self):
        return '/'.join([self.username, self.name])


class CoprProxy:
    def __init__(self, copr_url=COPR_API_URL):
        self.copr_url = copr_url[-1] == '/' and copr_url[:-1] or copr_url

    def _get(self, path):
        response = requests.get(self.copr_url + path)
        if response.status_code != 200:
            response.raise_for_status()
        return json.loads(response.text)

    def coprs(self, username):
        """ return list of coprs """
        data = self._get('/coprs/{}/'.format(username))
        if 'repos' in data:
            for copr in data['repos']:
                yield Copr(username=username, **copr)

    def copr(self, username, coprname):
        """ return copr details """
        for copr in self.coprs(username):
            if copr.name == coprname:
                return copr
        raise CoprException('Copr {}/{} does not exist.'.format(username, coprname))

