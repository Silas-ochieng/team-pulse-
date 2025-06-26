from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login as auth_login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.views.generic import CreateView
from django.urls import reverse_lazy, reverse
from django.contrib.auth.views import LoginView
from .serializers import UserSerializer, UserRegistrationSerializer, UserProfileUpdateSerializer
from .forms import CustomUserCreationForm, CustomUserChangeForm
from .models import CustomUser

# Get the User model
User = get_user_model()

class SignUpView(CreateView):
    model = CustomUser
    form_class = CustomUserCreationForm
    template_name = 'registration/signup.html'
    success_url = reverse_lazy('login')

class CustomLoginView(LoginView):
    template_name = 'users/login.html'
    redirect_authenticated_user = True

    def form_valid(self, form):
        user = form.get_user()
        if user.user_type == 'staff' and not user.is_approved:
            messages.error(self.request, 'Your account is pending admin approval.')
            logout(self.request)
            return redirect('users:login')
        return super().form_valid(form)

    def get_success_url(self):
        user = self.request.user
        if user.is_staff_user():
            return reverse('attendance:dashboard')
        elif user.is_community_member():
            return reverse('attendance:check_in_out')
        return reverse('users:profile')

def signup(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            # Set appropriate flags based on user type
            if user.user_type == 'staff':
                user.is_approved = False  # Requires admin approval
                user.is_staff = False     # Don't give admin access yet
                messages.success(request, 'Staff account created. Pending approval.')
            else:
                user.is_approved = True   # Auto-approve community members
                user.is_staff = False
                messages.success(request, 'Community account created!')
                auth_login(request, user)
                return redirect('attendance:check_in_out')
            user.save()
            return redirect('users:login')
    else:
        form = CustomUserCreationForm()

    return render(request, 'registration/signup.html', {'form': form, 'title': 'Sign Up'})

class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff_user():
            return User.objects.all()
        return User.objects.filter(id=self.request.user.id)

    def get_serializer_class(self):
        if self.action == 'create':
            return UserRegistrationSerializer
        elif self.action == 'update_profile':
            return UserProfileUpdateSerializer
        return UserSerializer

    @action(detail=False, methods=['put'])
    def update_profile(self, request):
        user = request.user
        serializer = self.get_serializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Profile Views
@login_required
def profile_view(request):
    return render(request, 'users/profile.html', {'user': request.user})

@login_required
def update_profile(request):
    if request.method == 'POST':
        form = CustomUserChangeForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('users:profile')
    else:
        form = CustomUserChangeForm(instance=request.user)
    return render(request, 'users/update_profile.html', {'form': form})

# Staff Management Views
@login_required
def staff_dashboard(request):
    if not request.user.is_staff_user():
        messages.error(request, 'Access restricted to approved staff members')
        return redirect('users:profile')
    return render(request, 'users/staff_dashboard.html')

@staff_member_required
def pending_approvals(request):
    pending_staff = CustomUser.objects.filter(
        user_type='staff', 
        is_approved=False
    ).order_by('date_joined')
    return render(request, 'users/pending_approvals.html', {
        'pending_staff': pending_staff
    })

@staff_member_required
def approve_staff(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id, user_type='staff')
    user.is_approved = True
    user.save()
    
    messages.success(request, f'{user.username} has been approved as staff!')
    return redirect('users:pending_approvals')
@login_required
def user_list(request):
    if not request.user.is_staff_user():
        messages.error(request, 'Access denied. Staff only.')
        return redirect('users:profile')
    users = CustomUser.objects.all()
    return render(request, 'users/user_list.html', {'users': users})