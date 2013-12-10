from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.core.exceptions import PermissionDenied

from openid.extensions import sreg

from .consumer import SUCCESS

class FasBackend(ModelBackend):
    def authenticate(self, response):
        if response.status != SUCCESS:
            raise PermissionDenied()
        User = get_user_model()
        response = sreg.SRegResponse.fromSuccessResponse(response)
        if not response:
            raise PermissionDenied()
        kwargs = { User.USERNAME_FIELD: response.get('nickname') }
        try:
            user = User.objects.get(**kwargs)
        except User.DoesNotExist:
            user = User(**kwargs)
        fullname = response.get('fullname', user.get_username())
        if hasattr(user, 'fullname'):
            user.fullname = fullname
        if hasattr(user, 'first_name') and hasattr(user, 'last_name'):
            try:
                user.first_name, user.last_name = fullname.rsplit(' ', 1)
            except ValueError:
                user.first_name, user.last_name = '', fullname
        if hasattr(user, 'email'):
            user.email = response.get('email', '')
        user.save()
        user.backend = 'django.contrib.auth.backends.ModelBackend'
        return user

