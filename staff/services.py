"""
Service helpers for staff registration package delivery operations.
Centralizes package payload building and QR readiness checks.
"""
import logging

from hotel.models import Hotel

logger = logging.getLogger(__name__)


def ensure_package_qr_ready(registration_code):
    """
    Ensure a RegistrationCode has both qr_token and qr_code_url.

    Generates token and/or QR image through canonical model methods
    if they are missing. Does not create a new package.

    Args:
        registration_code: RegistrationCode instance

    Returns:
        tuple: (success: bool, warnings: list[str])
    """
    warnings = []

    if not registration_code.qr_token:
        try:
            registration_code.generate_qr_token()
            warnings.append('QR token was missing and has been generated.')
            logger.info(
                'Generated missing qr_token for package %s (hotel=%s)',
                registration_code.id,
                registration_code.hotel_slug,
            )
        except Exception:
            logger.exception(
                'Failed to generate qr_token for package %s',
                registration_code.id,
            )
            return False, ['Failed to generate QR token.']

    if not registration_code.qr_code_url:
        try:
            registration_code.generate_qr_code()
            warnings.append('QR code image was missing and has been generated.')
            logger.info(
                'Generated missing qr_code_url for package %s (hotel=%s)',
                registration_code.id,
                registration_code.hotel_slug,
            )
        except Exception:
            logger.exception(
                'Failed to generate QR code for package %s',
                registration_code.id,
            )
            return False, ['Failed to generate QR code image.']

    return True, warnings


def _resolve_hotel_name(hotel_slug):
    """Resolve hotel name from slug, return slug as fallback."""
    try:
        return Hotel.objects.values_list('name', flat=True).get(slug=hotel_slug)
    except Hotel.DoesNotExist:
        return hotel_slug


def build_registration_package_payload(registration_code):
    """
    Build the canonical payload dict for a RegistrationCode.

    Single source of truth used by email, print, and API responses.

    Args:
        registration_code: RegistrationCode instance

    Returns:
        dict with id, code, qr_token, qr_code_url, registration_url,
        hotel_slug, hotel_name, created_at, used_at, status.
    """
    used = bool(registration_code.used_by or registration_code.used_at)
    return {
        'id': registration_code.id,
        'code': registration_code.code,
        'qr_token': registration_code.qr_token,
        'qr_code_url': registration_code.qr_code_url,
        'registration_url': registration_code.registration_url,
        'hotel_slug': registration_code.hotel_slug,
        'hotel_name': _resolve_hotel_name(registration_code.hotel_slug),
        'created_at': (
            registration_code.created_at.isoformat()
            if registration_code.created_at else None
        ),
        'used_at': (
            registration_code.used_at.isoformat()
            if registration_code.used_at else None
        ),
        'status': 'used' if used else 'unused',
    }
