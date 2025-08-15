from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from .models import Staff, RegistrationCode

# --- Token creation ---
@receiver(post_save, sender=User)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)

# --- Staff creation via registration code ---
@receiver(post_save, sender=User)
def create_staff_from_registration_code(sender, instance=None, created=False, **kwargs):
    if created:
        # Try to find a RegistrationCode linked to this user
        try:
            reg_code = RegistrationCode.objects.get(used_by=instance)
            # Create Staff if not already exists
            Staff.objects.get_or_create(user=instance, hotel_slug=reg_code.hotel_slug)
        except RegistrationCode.DoesNotExist:
            pass  # No registration code, no staff creation
