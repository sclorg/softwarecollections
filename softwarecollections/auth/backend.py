from django.contrib.auth.backends import ModelBackend

class PerObjectModelBackend(ModelBackend):
    """
    Authentication backend handling per object permissions
    """

    def has_perm(self, user, perm, obj=None):
        if not user.is_active:
            return False
        if obj is None:
            return perm in self.get_all_permissions(user)
        else:
            return hasattr(obj, 'has_perm') and obj.has_perm(user, perm)

