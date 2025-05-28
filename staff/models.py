from django.contrib.auth.models import User
from django.db import models

class Staff(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='staff_profile', null=True, blank=True)
    hotel = models.ForeignKey('hotel.Hotel', on_delete=models.CASCADE)

    DEPARTMENT_CHOICES = [
        ('front_office', 'Front Office'),
        ('front_house', 'Front House'),
        ('kitchen', 'Kitchen'),
        ('maintenance', 'Maintenance'),
        ('leisure', 'Leisure'),
        ('housekeeping', 'Housekeeping'),
        ('management', 'Management'),
    ]

    ROLE_CHOICES = [
        ('porter', 'Porter'),
        ('receptionist', 'Receptionist'),
        ('waiter', 'Waiter'),
        ('chef', 'Chef'),
        ('supervisor', 'Supervisor'),
        ('housekeeping_attendant', 'Housekeeping Attendant'),
        ('manager', 'Manager'),
        ('technician', 'Technician'),
    ]

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    department = models.CharField(max_length=20, choices=DEPARTMENT_CHOICES)
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, null=True, blank=True)
    position = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField(unique=True, null=True, blank=True)
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_on_duty = models.BooleanField(default=False)

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
