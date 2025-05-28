from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User

class HotelSubdomainBackend(ModelBackend):
    """
    Authenticates against username, password, and hotel subdomain.
    Allows superusers to login regardless of hotel.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        if request is None:
            return None

        hotel = getattr(request, 'hotel', None)

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return None

        if not user.check_password(password):
            return None

        # Superuser bypass: allow login regardless of hotel or None
        if user.is_superuser:
            return user

        # Normal user: must have staff_profile linked to current hotel
        if hasattr(user, 'staff_profile'):
            staff = user.staff_profile
            if hasattr(staff, 'hotel') and staff.hotel == hotel:
                return user

        return None
