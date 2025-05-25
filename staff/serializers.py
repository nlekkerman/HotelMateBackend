from django.contrib.auth.models import User
from rest_framework import serializers
from .models import Staff


class StaffMinimalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Staff
        fields = [
            'id',
            'first_name',
            'last_name',
            'department',
            'role',
            'position',
            'email',
            'phone_number',
            'is_active',
            'is_on_duty',
        ]
        # Note: no nested user field here to prevent recursion


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)
    staff_profile = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'is_active', 'password', 'staff_profile']
        extra_kwargs = {
            'username': {'required': True},
            'email': {'required': False},
            'is_active': {'required': False},
        }

    def get_staff_profile(self, obj):
        # Serialize the staff profile with minimal serializer to avoid recursion
        if hasattr(obj, 'staff_profile'):
            return StaffMinimalSerializer(obj.staff_profile).data
        return None

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = User(**validated_data)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password:
            instance.set_password(password)
        instance.save()
        return instance


class StaffSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = Staff
        fields = [
            'id',
            'user',
            'first_name',
            'last_name',
            'department',
            'role',
            'position',
            'email',
            'phone_number',
            'is_active',
            'is_on_duty',
        ]

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user = UserSerializer().create(user_data)
        staff = Staff.objects.create(user=user, **validated_data)
        return staff

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', None)
        if user_data and instance.user:
            user_serializer = UserSerializer(instance.user, data=user_data, partial=True)
            if user_serializer.is_valid(raise_exception=True):
                user_serializer.save()

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
