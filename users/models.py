# filepath: attendance_system/users/models.pyAdd commentMore actions
from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    USER_TYPE_CHOICES = (
        ('staff', 'Staff'),
        ('community', 'Community Member'),
    )
    
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES)
    phone_number = models.CharField(max_length=15)
    
    def is_staff_user(self):
        return self.user_type == 'staff'