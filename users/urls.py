from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from .views import CustomLoginView
from .views import SignUpView

app_name = 'users'

urlpatterns = [
    
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # User management
    path('signup/', SignUpView.as_view(), name='signup'),
    path('signup/', views.SignUpView.as_view(), name='signup'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/update/', views.update_profile, name='update_profile'),

     # Staff-only view
    path('list/', views.user_list, name='user_list'),  # Changed from 'users/'
]