"""
Hotel provisioning business logic.

This module is the canonical orchestration layer for creating a new hotel
with its primary admin user, staff profile, and optional registration
packages. All provisioning flows must go through provision_hotel().
"""
import logging
import secrets
import re

from django.contrib.auth.models import User
from django.db import transaction
from django.utils.text import slugify

from hotel.models import Hotel
from staff.models import Staff, RegistrationCode

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
    for the given hotel. Uses cryptographically-secure random generation.

    Returns list of dicts with code/qr_token/hotel_slug.
    Partial failures are captured as warnings.
    """
    results = []
    warnings = []

    for i in range(count):
        try:
            code = secrets.token_hex(4).upper()  # 8-char hex
            while RegistrationCode.objects.filter(code=code).exists():
                code = secrets.token_hex(4).upper()

            qr_token = secrets.token_urlsafe(32)
            while RegistrationCode.objects.filter(qr_token=qr_token).exists():
                qr_token = secrets.token_urlsafe(32)

            reg = RegistrationCode.objects.create(
                code=code,
                hotel_slug=hotel_slug,
                qr_token=qr_token,
            )
            reg.generate_qr_code()
            results.append({
                "code": reg.code,
                "qr_token": reg.qr_token,
                "qr_code_url": reg.qr_code_url,
            })
        except Exception as exc:
            logger.warning("Registration package %d/%d failed: %s", i + 1, count, exc)
            warnings.append(f"Package {i + 1} failed: {str(exc)}")

    return results, warnings


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

    # TODO: send password-setup email to admin_user (non-blocking)

    return {
        "hotel": hotel,
        "admin_user": admin_user,
        "staff": staff,
        "registration_packages": packages,
        "warnings": warnings,
    }
