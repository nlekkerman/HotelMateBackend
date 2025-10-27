from django.contrib.auth.models import User
from rest_framework import serializers
from .models import Staff, Department, Role, RegistrationCode
from hotel.serializers import HotelSerializer
from hotel.models import Hotel
from django.utils import timezone


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ['id', 'name', 'slug', 'description']


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ['id', 'name', 'slug', 'description']


class StaffMinimalSerializer(serializers.ModelSerializer):
    hotel = HotelSerializer(read_only=True)
    department = DepartmentSerializer(read_only=True)
    role = RoleSerializer(read_only=True)
    profile_image_url = serializers.SerializerMethodField()

    class Meta:
        model = Staff
        fields = [
            'id', 'first_name', 'last_name',
            'department', 'role',
            'email', 'phone_number',
            'is_active', 'is_on_duty',
            'hotel', 'profile_image_url',
        ]

    def get_profile_image_url(self, obj):
        url = obj.profile_image.url if obj.profile_image else None
        request = self.context.get('request')
        if url and request:
            return request.build_absolute_uri(url)
        return url


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)
    staff_profile = StaffMinimalSerializer(read_only=True)
    registration_code = serializers.CharField(write_only=True, required=False, allow_blank=True)
    used_registration_code = serializers.SerializerMethodField(read_only=True)
    staff_created = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'is_active',
            'password', 'staff_profile', 'registration_code',
            'used_registration_code', 'staff_created',
        ]
        extra_kwargs = {
            'username': {'required': True},
            'email': {'required': False},
            'is_active': {'required': False},
        }
    
    def get_used_registration_code(self, obj):
        code = RegistrationCode.objects.filter(used_by=obj).first()
        return code.code if code else None

    def get_staff_created(self, obj):
        # If staff_profile exists, consider "staff created" = Yes
        return "Yes" if hasattr(obj, 'staff_profile') else "No"

    def create(self, validated_data):
        reg_code_value = validated_data.pop('registration_code', None)
        password = validated_data.pop('password', None)

        # Create User
        user = User(**validated_data)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save()

        # Handle registration code
        if reg_code_value:
            try:
                reg_code = RegistrationCode.objects.get(code=reg_code_value, used_by__isnull=True)
            except RegistrationCode.DoesNotExist:
                raise serializers.ValidationError({'registration_code': 'Invalid or already used code.'})
            reg_code.used_by = user
            reg_code.used_at = timezone.now()
            reg_code.save()

            # Optional: assign hotel to user/staff if you have a Staff object
            Staff.objects.create(user=user, hotel_slug=reg_code.hotel_slug)

        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        reg_code_value = validated_data.pop('registration_code', None)

        # Update user fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()

        # Optionally handle registration code updates
        if reg_code_value:
            try:
                reg_code = RegistrationCode.objects.get(code=reg_code_value, used_by__isnull=True)
            except RegistrationCode.DoesNotExist:
                raise serializers.ValidationError({'registration_code': 'Invalid or already used code.'})
            reg_code.used_by = instance
            reg_code.used_at = timezone.now()
            reg_code.save()

        return instance


# Firebase FCM Token serializer removed


class StaffSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    hotel = serializers.PrimaryKeyRelatedField(queryset=Hotel.objects.all())
    hotel_name = serializers.CharField(source='hotel.name', read_only=True)

    department = serializers.PrimaryKeyRelatedField(
        queryset=Department.objects.all(),
        allow_null=True,
        required=False,
    )
    role = serializers.PrimaryKeyRelatedField(
        queryset=Role.objects.all(),
        allow_null=True,
        required=False,
    )

    department_detail = DepartmentSerializer(source='department', read_only=True)
    role_detail = RoleSerializer(source='role', read_only=True)

    access_level = serializers.ChoiceField(choices=Staff.ACCESS_LEVEL_CHOICES)
    allowed_navs = serializers.SerializerMethodField()
    # Firebase FCM tokens removed
    has_registered_face = serializers.BooleanField()
    profile_image = serializers.ImageField(required=False, allow_null=True, use_url=True)
    profile_image_url = serializers.CharField(source='profile_image.url', read_only=True)

    class Meta:
        model = Staff
        fields = [
            'id', 'user', 'first_name', 'last_name',
            'department', 'department_detail',
            'role', 'role_detail',
            'email', 'phone_number',
            'is_active', 'is_on_duty',
            'hotel', 'access_level', 'hotel_name',
            'profile_image', 'profile_image_url',
            'has_registered_face', 'allowed_navs',
        ]
        read_only_fields = ['user', 'allowed_navs', 'hotel_name', 'profile_image_url', 'department_detail', 'role_detail']

    def get_allowed_navs(self, obj):
        if not obj.role or not obj.access_level:
            return []

        # Define allowed navs by role slug
        role_nav_map = {
            'porter': ['room_service', 'home'],
            'chef': ['stock_dashboard', 'home'],
            'manager': ['stock_dashboard', 'staff', 'roster', 'settings', 'home'],
            'receptionist': ['reception', 'rooms', 'guests', 'home'],
            'staff_admin': ['staff', 'good_to_know', 'home'],
            'super_staff_admin': ['staff', 'good_to_know', 'settings', 'home'],
            # Add other roles as needed
        }

        # Define allowed navs by access level
        access_level_nav_map = {
            'super_staff_admin': ['settings', 'staff', 'roster', 'home', 'good_to_know'],
            'staff_admin': ['staff', 'good_to_know', 'home'],
            'regular_staff': [],  # no extra navs
        }

        role_slug = obj.role.slug.lower()
        navs_for_role = role_nav_map.get(role_slug, ['home'])
        navs_for_access = access_level_nav_map.get(obj.access_level, [])

        # Union of role navs and access level navs
        allowed_navs = list(set(navs_for_role) | set(navs_for_access))
        return allowed_navs

    def create(self, validated_data):
        user_data = validated_data.pop('user', None)
        if user_data:
            user = UserSerializer().create(user_data)
        else:
            raise serializers.ValidationError({'user': 'User data is required to create staff.'})
        staff = Staff.objects.create(user=user, **validated_data)
        return staff

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', None)
        if user_data and instance.user:
            user_serializer = UserSerializer(instance.user, data=user_data, partial=True)
            user_serializer.is_valid(raise_exception=True)
            user_serializer.save()

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class StaffLoginInputSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)


class StaffLoginOutputSerializer(serializers.Serializer):
    username = serializers.CharField()
    token = serializers.CharField()
    hotel_id = serializers.IntegerField(allow_null=True, required=False)
    hotel_name = serializers.CharField(allow_null=True, required=False)
    hotel_slug = serializers.CharField(allow_null=True, required=False)
    is_staff = serializers.BooleanField()
    is_superuser = serializers.BooleanField()
    access_level = serializers.CharField(allow_null=True, required=False)
    hotel = serializers.DictField(required=False)
    allowed_navs = serializers.ListField(child=serializers.CharField(), default=list)
    profile_image_url = serializers.CharField(allow_null=True, required=False)
    role = serializers.CharField(allow_null=True, required=False)
    department = serializers.CharField(allow_null=True, required=False)
    staff_id = serializers.IntegerField(allow_null=True, required=False)


class RegisterStaffSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(write_only=True)
    hotel = serializers.PrimaryKeyRelatedField(queryset=Hotel.objects.all())
    hotel_name = serializers.CharField(source='hotel.name', read_only=True)
    access_level = serializers.ChoiceField(choices=Staff.ACCESS_LEVEL_CHOICES)
    user = UserSerializer(read_only=True)
    # Firebase FCM tokens removed
    profile_image = serializers.ImageField(required=False, allow_null=True)
    department = serializers.PrimaryKeyRelatedField(
        queryset=Department.objects.all(),
        allow_null=True,
        required=False,
    )
    role = serializers.PrimaryKeyRelatedField(
        queryset=Role.objects.all(),
        allow_null=True,
        required=False,
    )

    class Meta:
        model = Staff
        fields = [
            'id', 'user_id', 'user', 'first_name', 'last_name',
            'department', 'role',
            'email', 'phone_number', 'is_active', 'is_on_duty',
            'hotel', 'access_level', 'hotel_name',
            'profile_image',
        ]

    def create(self, validated_data):
        user_id = validated_data.pop('user_id')
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise serializers.ValidationError({'user_id': 'User not found.'})
        if Staff.objects.filter(user=user).exists():
            raise serializers.ValidationError({'user_id': 'Staff already exists for this user.'})
        staff = Staff.objects.create(user=user, **validated_data)
        return staff
