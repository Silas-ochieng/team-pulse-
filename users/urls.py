from django.urls import path #Add commentMore actions
from . import views
from django.contrib.auth import views as auth_views
from .views import CustomLoginView

app_name = 'users'

urlpatterns = [
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # User management
    path('signup/', views.SignUpView.as_view(), name='signup'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/<int:user_id>/', views.profile_view, name='profile'), 
    path('profile/update/', views.update_profile, name='update_profile'),

     # Staff-only view
    path('dashboard/', views.staff_dashboard, name='dashboard'),
    path('list/', views.user_list, name='user_list'),
    path('profile/password/', auth_views.PasswordChangeView.as_view(
        template_name='registration/password_change_form.html'
    ), name='password_change'),
    path('profile/password/done/', auth_views.PasswordChangeDoneView.as_view(
        template_name='registration/password_change_done.html'
    ), name='password_change_done'), 
    path('pending-approvals/', views.pending_approvals, name='pending_approvals'),
    path('approve-staff/<int:user_id>/', views.approve_staff, name='approve_staff'),] # Changed from 'users/'
     # For specific user
# This URL pattern is for listing all users, accessible only to staff members
# The view will check if the user is a staff member before displaying the list