from django.contrib.auth.models import User
from django.db import models
from cloudinary.models import CloudinaryField


class NavigationItem(models.Model):
    """
    Navigation links that can be assigned to staff members.
    Each hotel can have different navigation items.
    Only Django superuser can create/edit these.
    Super Staff Admin assigns them to staff members within their hotel.
    """
    hotel = models.ForeignKey(
        'hotel.Hotel',
        on_delete=models.CASCADE,
        related_name='navigation_items',
        help_text="Hotel this navigation item belongs to"
    )
    name = models.CharField(
        max_length=100,
        help_text="Display name (e.g., 'Home', 'Chat')"
    )
    slug = models.SlugField(
        max_length=100,
        help_text="Unique identifier (e.g., 'home', 'chat')"
    )
    path = models.CharField(
        max_length=255,
        help_text="Frontend route (e.g., '/', '/chat')"
    )
    description = models.TextField(
        blank=True,
        null=True,
        help_text="What this navigation link does"
    )
    display_order = models.IntegerField(
        default=0,
        help_text="Order in navigation menu"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this link is currently active"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.hotel.slug} - {self.name}"

    class Meta:
        ordering = ['hotel', 'display_order', 'name']
        unique_together = [['hotel', 'slug']]
        verbose_name = 'Navigation Item'
        verbose_name_plural = 'Navigation Items'


class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class Role(models.Model):
    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name='roles',
        null=True,
        blank=True
    )
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class Staff(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='staff_profile',
        null=True,
        blank=True
    )
    hotel = models.ForeignKey('hotel.Hotel', on_delete=models.CASCADE)

    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='staff_members'
    )

    role = models.ForeignKey(
        Role,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='staff_members'
    )

    ACCESS_LEVEL_CHOICES = [
        ('staff_admin', 'Staff Admin'),
        ('super_staff_admin', 'Super Staff Admin'),
        ('regular_staff', 'Regular Staff'),
    ]
    access_level = models.CharField(
        max_length=20,
        choices=ACCESS_LEVEL_CHOICES,
        default='regular_staff'
    )

    first_name = models.CharField(max_length=100, blank=True, default='')
    last_name = models.CharField(max_length=100, blank=True, default='')

    email = models.EmailField(unique=True, null=True, blank=True)
    phone_number = models.CharField(max_length=15, null=True, blank=True)

    is_active = models.BooleanField(default=True)
    is_on_duty = models.BooleanField(default=False)
    has_registered_face = models.BooleanField(default=False, null=True)

    # Firebase Cloud Messaging token for push notifications
    fcm_token = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Firebase device token for push notifications"
    )

    profile_image = CloudinaryField(
        "profile image",
        blank=True,
        null=True,
        folder="hotel_staff_profiles/",
        transformation={
            "width": 200,
            "height": 200,
            "crop": "thumb",
            "gravity": "face"
        }
    )

    # Navigation permissions - assigned by super_staff_admin
    allowed_navigation_items = models.ManyToManyField(
        NavigationItem,
        blank=True,
        related_name='staff_members',
        help_text="Navigation links this staff member can access"
    )

    def __str__(self):
        department_name = self.department.name if self.department else "No Department"
        role_name = self.role.name if self.role else "No Role"
        return f"{self.first_name} {self.last_name} - {department_name} - {role_name}"

    @classmethod
    def get_staff_by_role(cls, role):
        # Accept Role instance, slug, or name
        if isinstance(role, Role):
            return cls.objects.filter(role=role, is_active=True)
        return cls.objects.filter(role__slug=role, is_active=True)

    @classmethod
    def get_by_department(cls, department):
        # Accept Department instance or slug
        if isinstance(department, Department):
            return cls.objects.filter(department=department, is_active=True)
        return cls.objects.filter(department__slug=department, is_active=True)

    class Meta:
        ordering = ['department__name', 'last_name']


class RegistrationCode(models.Model):
    code = models.CharField(max_length=20, unique=True)
    hotel_slug = models.SlugField(max_length=50)  # identifies the hotel
    used_by = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    used_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.code} - {self.hotel_slug}" + (f" (Used by {self.used_by.username})" if self.used_by else "")

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    registration_code = models.OneToOneField(
        "staff.RegistrationCode",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='user_profile'
    )

    def __str__(self):
        return f"{self.user.username} profile"