from django.db import models

class Staff(models.Model):
    DEPARTMENT_CHOICES = [
        ('front_office', 'Front Office'),
        ('front_house', 'Front House'),
        ('kitchen', 'Kitchen'),
        ('maintenance', 'Maintenance'),
        ('leisure', 'Leisure'),
        ('housekeeping', 'Housekeeping'),
        ('management', 'Management'),
    ]

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    department = models.CharField(max_length=20, choices=DEPARTMENT_CHOICES)
    position = models.CharField(max_length=100, blank=True, null=True)  # Optional position/job title
    email = models.EmailField(unique=True, null=True, blank=True)
    phone_number = models.CharField(max_length=15, null=True, blank=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.get_department_display()}"
