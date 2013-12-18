from django.conf import settings

from openid.extensions import sreg
from openid.consumer.consumer import \
    Consumer as _Consumer, SUCCESS, CANCEL, FAILURE, SETUP_NEEDED

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
