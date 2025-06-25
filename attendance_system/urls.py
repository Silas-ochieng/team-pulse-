from django.contrib import admin #Add commentMore actions
from django.urls import path, include
from django.views.generic import RedirectView  # Add this import
from rest_framework.routers import DefaultRouter
from users.views import UserViewSet
from django.conf import settings
from django.conf.urls.static import static

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')

urlpatterns = [
    
    path('', RedirectView.as_view(pattern_name='attendance:dashboard'), name='home'),
    path('admin/', admin.site.urls),
    path('attendance/', include(('attendance.urls', 'attendance'), namespace='attendance')),
    path('accounts/', include('django.contrib.auth.urls')),
    path('users/', include('users.urls')),
    path('api/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls')),
    

]
    