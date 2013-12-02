"""
FAS OpenID backend
"""
from social.backends.open_id import OpenIdAuth

SREG_NAMES = [
    ('email', 'email'),
    ('fullname', 'fullname'),
    ('nickname', 'username'),
]

class FasOpenId(OpenIdAuth):
    name = 'FAS'
    URL = 'https://id.fedoraproject.org'

    def get_user_details(self, response):
        # get values using SimpleRegistration values
        values = self.values_from_response(response, sreg_names=SREG_NAMES)
        try:
            values['first_name'], values['last_name'] = values['fullname'].rsplit(' ', 1)
        except ValueError:
            values['last_name'] = values['fullname']
        return values

