# users/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    USER_TYPE_CHOICES = (
        ('staff', 'Staff'),
        ('community', 'Community Member'),
    )
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES)
    phone_number = models.CharField(max_length=15)
    is_approved = models.BooleanField(default=False)
    
    def is_staff_user(self):
        """Returns True if user is approved staff member"""
        return self.user_type == 'staff' and self.is_approved
    
    def is_community_member(self):
        return self.user_type == 'community'
    
    # Add this to make admin approval workflow clearer
    @property
    def needs_approval(self):
        return self.user_type == 'staff' and not self.is_approved