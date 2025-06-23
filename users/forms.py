from django import forms ## Add commentMore actions
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import CustomUser

class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ('username', 'email', 'user_type', 'phone_number')

class CustomUserChangeForm(UserChangeForm):
    password = None  # Remove password field from update form
    
    class Meta:
        model = CustomUser
        fields = ('email', 'phone_number', 'first_name', 'last_name')