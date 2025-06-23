from django.contrib import admin #Add commentMore actions
from django.urls import path, include
from django.views.generic import RedirectView  # Add this import
from rest_framework.routers import DefaultRouter
from users.views import UserViewSet

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')

urlpatterns = [
    path('', RedirectView.as_view(pattern_name='attendance:dashboard'), name='home'),  # Redirect to the dashboard
    path('', RedirectView.as_view(url='accounts/login/')),
    path('admin/', admin.site.urls),
    path('attendance/', include(('attendance.urls', 'attendance'), namespace='attendance')),
    path('accounts/', include('django.contrib.auth.urls')),   # Changed from empty path
    path('users/', include('users.urls')),  # Changed from empty path,
    path('api/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls')),
]
    