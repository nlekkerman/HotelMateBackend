"""
Serializers for hotel provisioning endpoint.
"""
from rest_framework import serializers
from django.contrib.auth.models import User

from hotel.models import Hotel
from staff.models import Staff


class HotelProvisioningInputSerializer(serializers.Serializer):
    """Nested 'hotel' block inside the provisioning request."""
    name = serializers.CharField(max_length=255)
    slug = serializers.SlugField(max_length=50, required=False, allow_blank=True)
    subdomain = serializers.SlugField(max_length=50, required=False, allow_blank=True)
    city = serializers.CharField(max_length=120, required=False, allow_blank=True)
    country = serializers.CharField(max_length=120, required=False, allow_blank=True)
    timezone = serializers.CharField(max_length=50, required=False, default="Europe/Dublin")
    email = serializers.EmailField(required=False, allow_blank=True)
    phone = serializers.CharField(max_length=30, required=False, allow_blank=True)


class PrimaryAdminInputSerializer(serializers.Serializer):
    """Nested 'primary_admin' block."""
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    email = serializers.EmailField()


class RegistrationPackagesInputSerializer(serializers.Serializer):
    """Optional 'registration_packages' block."""
    generate_count = serializers.IntegerField(
        required=False, default=0, min_value=0, max_value=10
    )


class ProvisionHotelRequestSerializer(serializers.Serializer):
    """
    Top-level request serializer for POST /api/hotels/provision/.
    """
    hotel = HotelProvisioningInputSerializer()
    primary_admin = PrimaryAdminInputSerializer()
    registration_packages = RegistrationPackagesInputSerializer(required=False, default={})

    def validate_hotel(self, value):
        slug = value.get("slug")
        if slug and Hotel.objects.filter(slug=slug).exists():
            raise serializers.ValidationError(
                {"slug": "A hotel with this slug already exists."}
            )

        subdomain = value.get("subdomain")
        if subdomain and Hotel.objects.filter(subdomain=subdomain).exists():
            raise serializers.ValidationError(
                {"subdomain": "A hotel with this subdomain already exists."}
            )

        # If no slug provided, check the auto-generated one too
        if not slug:
            from django.utils.text import slugify
            auto_slug = slugify(value["name"])
            if Hotel.objects.filter(slug=auto_slug).exists():
                raise serializers.ValidationError(
                    {"slug": f"Auto-generated slug '{auto_slug}' already exists. Provide a unique slug."}
                )

        return value

    def validate_primary_admin(self, value):
        email = value["email"]
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError(
                {"email": "A user with this email already exists."}
            )
        if Staff.objects.filter(email=email).exists():
            raise serializers.ValidationError(
                {"email": "A staff profile with this email already exists."}
            )
        return value


class ProvisionHotelResponseSerializer(serializers.Serializer):
    """Response serializer for the provisioning endpoint."""
    hotel_id = serializers.IntegerField()
    hotel_slug = serializers.CharField()
    hotel_name = serializers.CharField()
    admin_user_id = serializers.IntegerField()
    admin_username = serializers.CharField()
    admin_email = serializers.EmailField()
    staff_id = serializers.IntegerField()
    access_level = serializers.CharField()
    registration_packages = serializers.ListField(child=serializers.DictField(), required=False)
    warnings = serializers.ListField(child=serializers.CharField(), required=False)
