"""
Service helpers for staff registration package delivery operations.
Centralizes QR readiness checks and provides a single serializer-based
payload builder.
"""
import logging

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


def serialize_package(registration_code, hotel=None):
    """
    Return the canonical dict representation of a RegistrationCode.

    Thin wrapper around RegistrationCodeSerializer — the single source
    of truth for package field mapping.  All consumers (GET list, POST
    create, email, print) must use this or the serializer directly.

    Args:
        registration_code: RegistrationCode instance
        hotel: optional Hotel instance to avoid extra DB lookup for hotel_name

    Returns:
        dict (serializer.data)
    """
    from .serializers import RegistrationCodeSerializer
    context = {}
    if hotel is not None:
        context['hotel'] = hotel
    return RegistrationCodeSerializer(registration_code, context=context).data
