"""
Shared Cloudinary upload utilities.
Reuses the existing Cloudinary integration from maintenance app.
"""
from cloudinary.models import CloudinaryField
from rest_framework import serializers


class CloudinaryImageSerializer(serializers.Serializer):
    """
    Reusable serializer for Cloudinary image uploads.
    Can be used in any serializer that needs image upload.
    """
    image = serializers.ImageField(required=True)
    
    def validate_image(self, value):
        """Validate image file"""
        # Max 10MB
        max_size = 10 * 1024 * 1024
        if value.size > max_size:
            raise serializers.ValidationError(
                "Image file too large. Maximum size is 10MB."
            )
        
        # Check file type
        allowed_types = ['image/jpeg', 'image/png', 'image/jpg', 'image/webp']
        if value.content_type not in allowed_types:
            raise serializers.ValidationError(
                f"Invalid image type. Allowed types: {', '.join(allowed_types)}"
            )
        
        return value


class BulkCloudinaryImageSerializer(serializers.Serializer):
    """
    Serializer for bulk image uploads (galleries, etc).
    Similar to maintenance BulkMaintenancePhotoSerializer.
    """
    images = serializers.ListField(
        child=serializers.ImageField(),
        write_only=True,
        min_length=1,
        max_length=20  # Max 20 images at once
    )
    
    def validate_images(self, value):
        """Validate each image in the list"""
        max_size = 10 * 1024 * 1024
        allowed_types = ['image/jpeg', 'image/png', 'image/jpg', 'image/webp']
        
        for image in value:
            if image.size > max_size:
                raise serializers.ValidationError(
                    f"Image {image.name} is too large. Maximum size is 10MB."
                )
            if image.content_type not in allowed_types:
                raise serializers.ValidationError(
                    f"Image {image.name} has invalid type. Allowed: JPEG, PNG, WebP"
                )
        
        return value


def get_cloudinary_url(cloudinary_field):
    """
    Get URL from a CloudinaryField.
    Returns None if field is empty.
    
    Args:
        cloudinary_field: A CloudinaryField instance
        
    Returns:
        str or None: The Cloudinary URL or None
    """
    if cloudinary_field:
        return cloudinary_field.url
    return None


def get_cloudinary_public_id(cloudinary_field):
    """
    Extract public_id from a CloudinaryField.
    Useful for deletions or transformations.
    
    Args:
        cloudinary_field: A CloudinaryField instance
        
    Returns:
        str or None: The Cloudinary public_id or None
    """
    if cloudinary_field:
        return cloudinary_field.public_id
    return None
