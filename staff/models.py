from django.contrib.auth.models import User
from django.db import models
from cloudinary.models import CloudinaryField


class Staff(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='staff_profile', null=True, blank=True)
    hotel = models.ForeignKey('hotel.Hotel', on_delete=models.CASCADE)

    DEPARTMENT_CHOICES = [
        ('reception', 'Reception'),
        ('kitchen', 'Kitchen'),
        ('housekeeping', 'Housekeeping'),
        ('porters', 'Porters'),
        ('maintenance', 'Maintenance'),
        ('leisure', 'Leisure'),
        ('spa', 'Spa'),
        ('security', 'Security'),
        ('management', 'Management'),
        ('food_and_beverage', 'Food & Beverage'),
        ('cleaning', 'Cleaning Crew'),
        ('front_office', 'Front Office'),
    ]


    ROLE_CHOICES = [
        ('porter', 'Porter'),
        ('receptionist', 'Receptionist'),
        ('waiter', 'Waiter'),
        ('bartender', 'Bartender'),
        ('chef', 'Chef'),
        ('supervisor', 'Supervisor'),
        ('housekeeping_attendant', 'Housekeeping Attendant'),
        ('manager', 'Manager'),
        ('technician', 'Technician'),
        ('security', 'Security'),
        ('concierge', 'Concierge'),
        ('leisure_staff', 'Leisure Staff'),
        ('maintenance_staff', 'Maintenance Staff'),
        ('other', 'Other'),
    ]
    
    ACCESS_LEVEL_CHOICES = [
        ('staff_admin', 'Staff Admin'),
        ('super_staff_admin', 'Super Staff Admin'),
        ('regular_staff', 'Regular Staff'),
    ]

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    department = models.CharField(max_length=20, choices=DEPARTMENT_CHOICES)
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, null=True, blank=True)
    access_level = models.CharField(max_length=20, choices=ACCESS_LEVEL_CHOICES, default='regular_staff')
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
        return f"{self.first_name} {self.last_name} - {self.get_department_display()}"

    @classmethod
    def get_staff_by_role(cls, role):
        return cls.objects.filter(role=role, is_active=True)

    @classmethod
    def get_by_department(cls, department):
        return cls.objects.filter(department=department, is_active=True)

    class Meta:
        ordering = ['department', 'last_name']

class StaffFCMToken(models.Model):
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name='fcm_tokens')
    token = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(auto_now=True)