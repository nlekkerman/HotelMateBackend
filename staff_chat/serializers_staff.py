"""
Serializers for Staff model in chat context
"""
from rest_framework import serializers
from staff.models import Staff


class StaffBasicSerializer(serializers.ModelSerializer):
    """
    Basic staff info for chat UI
    """
    full_name = serializers.SerializerMethodField()
    avatar_url = serializers.SerializerMethodField()
    role_name = serializers.SerializerMethodField()
    department_name = serializers.SerializerMethodField()
    is_online = serializers.BooleanField(
        source='is_on_duty',
        read_only=True
    )

    class Meta:
        model = Staff
        fields = [
            'id',
            'first_name',
            'last_name',
            'full_name',
            'email',
            'avatar_url',
            'role_name',
            'department_name',
            'is_online',
            'is_on_duty'
        ]
        read_only_fields = fields

    def get_full_name(self, obj):
        """Get staff member's full name"""
        return f"{obj.first_name} {obj.last_name}".strip()

    def get_avatar_url(self, obj):
        """Get avatar/profile image URL"""
        if obj.profile_image and hasattr(obj.profile_image, 'url'):
            return obj.profile_image.url
        return None

    def get_role_name(self, obj):
        """Get role display name"""
        return obj.role.name if obj.role else None

    def get_department_name(self, obj):
        """Get department display name"""
        return obj.department.name if obj.department else None


class StaffChatProfileSerializer(serializers.ModelSerializer):
    """
    Detailed staff profile for chat participant display
    """
    full_name = serializers.SerializerMethodField()
    avatar_url = serializers.SerializerMethodField()
    role_name = serializers.SerializerMethodField()
    role_slug = serializers.SerializerMethodField()
    department_name = serializers.SerializerMethodField()
    department_slug = serializers.SerializerMethodField()
    is_online = serializers.BooleanField(
        source='is_on_duty',
        read_only=True
    )
    last_seen = serializers.DateTimeField(
        source='last_activity',
        read_only=True
    )

    class Meta:
        model = Staff
        fields = [
            'id',
            'first_name',
            'last_name',
            'full_name',
            'email',
            'phone_number',
            'avatar_url',
            'role_name',
            'role_slug',
            'department_name',
            'department_slug',
            'is_online',
            'is_on_duty',
            'last_seen'
        ]
        read_only_fields = fields

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()

    def get_avatar_url(self, obj):
        if obj.profile_image and hasattr(obj.profile_image, 'url'):
            return obj.profile_image.url
        return None

    def get_role_name(self, obj):
        return obj.role.name if obj.role else None

    def get_role_slug(self, obj):
        return obj.role.slug if obj.role else None

    def get_department_name(self, obj):
        return obj.department.name if obj.department else None

    def get_department_slug(self, obj):
        return obj.department.slug if obj.department else None
