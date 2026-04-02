"""
Hotel provisioning business logic.

This module is the canonical orchestration layer for creating a new hotel
with its primary admin user, staff profile, and optional registration
packages. All provisioning flows must go through provision_hotel().
"""
import logging
import re

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.db import transaction
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils.text import slugify

from hotel.models import Hotel
from staff.models import Staff, RegistrationCode, Department, Role

logger = logging.getLogger(__name__)


def derive_username(email: str, hotel_slug: str) -> str:
    """
    Deterministic username from email + hotel slug.
    Example: jane.obrien@grand.com + the-grand-dublin → jane.obrien_the-grand-dublin
    If that collides, append a short random suffix.
    """
    local_part = email.split("@")[0]
    # Sanitise: keep alphanumeric, dots, hyphens, underscores
    local_part = re.sub(r"[^\w.\-]", "", local_part)
    base = f"{local_part}_{hotel_slug}"[:145]  # Django max 150
    username = base
    suffix = 0
    while User.objects.filter(username=username).exists():
        suffix += 1
        username = f"{base}_{suffix}"
    return username


def generate_registration_packages(hotel_slug: str, count: int) -> list:
    """
    Generate *count* registration packages (RegistrationCode + QR token)
    for the given hotel.

    Delegates all code/token/QR creation to the canonical
    RegistrationCode.create_package() class method.

    Returns (results, warnings) where results is a list of dicts with
    code/qr_token/qr_code_url/registration_url/hotel_slug.
    Partial failures are captured as warnings.
    """
    results = []
    warnings = []

    for i in range(count):
        try:
            pkg = RegistrationCode.create_package(hotel_slug)
            results.append(pkg)
        except Exception as exc:
            logger.warning("Registration package %d/%d failed: %s", i + 1, count, exc)
            warnings.append(f"Package {i + 1} failed: {str(exc)}")

    return results, warnings


def _send_admin_setup_email(user, hotel):
    """
    Send a password-setup email to the newly provisioned admin.
    Uses the same token mechanism as PasswordResetConfirmView.
    Non-critical: logs warning on failure, never raises.
    """
    try:
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        base_url = getattr(settings, 'FRONTEND_BASE_URL', 'https://hotelsmates.com')
        setup_url = f"{base_url}/reset-password/{uid}/{token}/"

        message = (
            f"Welcome to HotelsMates!\n\n"
            f"Hello {user.first_name},\n\n"
            f"You have been set up as the primary administrator for {hotel.name}.\n\n"
            f"Please set your password by clicking the link below:\n"
            f"{setup_url}\n\n"
            f"This link will expire in 24 hours.\n\n"
            f"Your username: {user.username}\n"
            f"Hotel: {hotel.name} ({hotel.slug})\n\n"
            f"Best regards,\n"
            f"HotelsMates Team"
        )

        send_mail(
            subject=f"HotelsMates - Complete your account setup for {hotel.name}",
            message=message,
            from_email=f"HotelsMates Team <{settings.EMAIL_HOST_USER}>",
            recipient_list=[user.email],
        )
        logger.info("Sent admin setup email to %s for hotel %s", user.email, hotel.slug)
        return True
    except Exception as exc:
        logger.warning("Failed to send admin setup email to %s: %s", user.email, exc)
        return False


def provision_hotel(validated_data: dict) -> dict:
    """
    Atomic provisioning of hotel + primary admin.

    validated_data shape (already validated by serializer):
    {
        "hotel": { "name", "slug"?, "subdomain"?, "city"?, ... },
        "primary_admin": { "first_name", "last_name", "email" },
        "registration_packages": { "generate_count"?: int },
    }

    Returns a result dict with hotel, admin user, staff, packages, warnings.
    """
    hotel_data = validated_data["hotel"]
    admin_data = validated_data["primary_admin"]
    pkg_data = validated_data.get("registration_packages", {})
    generate_count = pkg_data.get("generate_count", 0)

    # Resolve optional department/role
    department = None
    role = None
    department_id = admin_data.get("department_id")
    role_id = admin_data.get("role_id")
    if department_id is not None:
        department = Department.objects.get(id=department_id)
    if role_id is not None:
        role = Role.objects.get(id=role_id)

    # Auto-generate slug if not provided
    slug = hotel_data.get("slug") or slugify(hotel_data["name"])

    # --- Atomic: hotel + user + staff ---
    with transaction.atomic():
        hotel = Hotel.objects.create(
            name=hotel_data["name"],
            slug=slug,
            subdomain=hotel_data.get("subdomain") or None,
            city=hotel_data.get("city", ""),
            country=hotel_data.get("country", ""),
            timezone=hotel_data.get("timezone", "Europe/Dublin"),
            email=hotel_data.get("email", ""),
            phone=hotel_data.get("phone", ""),
        )
        # post_save signal creates all related config objects

        username = derive_username(admin_data["email"], hotel.slug)
        admin_user = User.objects.create_user(
            username=username,
            email=admin_data["email"],
            first_name=admin_data["first_name"],
            last_name=admin_data["last_name"],
        )
        admin_user.set_unusable_password()
        admin_user.is_staff = True
        admin_user.is_superuser = False
        admin_user.save()

        staff = Staff.objects.create(
            user=admin_user,
            hotel=hotel,
            first_name=admin_data["first_name"],
            last_name=admin_data["last_name"],
            email=admin_data["email"],
            department=department,
            role=role,
            access_level="super_staff_admin",
            is_active=True,
        )

    # --- Post-transaction work (non-critical) ---
    warnings = []

    # Registration packages
    packages = []
    if generate_count > 0:
        packages, pkg_warnings = generate_registration_packages(hotel.slug, generate_count)
        warnings.extend(pkg_warnings)

    # Send password-setup email to admin
    if not _send_admin_setup_email(admin_user, hotel):
        warnings.append("Failed to send admin setup email. Admin can use password reset later.")

    return {
        "hotel": hotel,
        "admin_user": admin_user,
        "staff": staff,
        "registration_packages": packages,
        "warnings": warnings,
    }
