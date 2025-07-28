from django.contrib.auth.models import User
from django.db import models
from cloudinary.models import CloudinaryField


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

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)

    email = models.EmailField(unique=True, null=True, blank=True)
    phone_number = models.CharField(max_length=15, null=True, blank=True)

    is_active = models.BooleanField(default=True)
    is_on_duty = models.BooleanField(default=False)
    has_registered_face = models.BooleanField(default=False, null=True)

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


class StaffFCMToken(models.Model):
    staff = models.ForeignKey(
        Staff,
        on_delete=models.CASCADE,
        related_name='fcm_tokens'
    )
    token = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"FCM Token for {self.staff}"    
