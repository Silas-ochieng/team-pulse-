"""
URL configuration for attendance_system project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView  # Add this import
from rest_framework.routers import DefaultRouter
from users.views import UserViewSet
from django.contrib.auth.views import LogoutView


router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')

urlpatterns = [
    path('', RedirectView.as_view(pattern_name='attendance:dashboard'), name='home'),  # Redirect to the dashboard
    path('', RedirectView.as_view(url='accounts/login/')),
    path('accounts/logout/', LogoutView.as_view(http_method_names=['get', 'post']), name='logout'),  # Changed from empty path
    path('admin/', admin.site.urls),
    path('attendance/', include(('attendance.urls', 'attendance'), namespace='attendance')),
    path('accounts/', include('django.contrib.auth.urls')),   # Changed from empty path
    path('users/', include('users.urls')),  # Changed from empty path,
    path('api/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls')),
    
]