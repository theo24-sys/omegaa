from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()

class PhoneNumberBackend:
    """
    Authenticate using either phone_number or username with password.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        # 'username' parameter might contain the phone number or the actual username.
        try:
            user = User.objects.get(Q(phone_number=username) | Q(username=username))
            if user.check_password(password) and self.user_can_authenticate(user):
                return user
        except User.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
             return None

    def user_can_authenticate(self, user):
        """
        Reject users with is_active=False.
        """
        return getattr(user, 'is_active', True)
