from django.shortcuts import render, redirect #Add commentMore actions
from django.contrib.auth import login, authenticate, get_user_model  # Added get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.views.generic import CreateView
from django.urls import reverse_lazy
from .serializers import UserSerializer, UserRegistrationSerializer, UserProfileUpdateSerializer
from .forms import CustomUserCreationForm, CustomUserChangeForm
from django.contrib.auth.views import LoginView

# Get the User model
User = get_user_model()  # Added this line

class CustomLoginView(LoginView):
    template_name = 'users/login.html'  # This points to your custom template
    redirect_authenticated_user = True  # Redirects if user is already logged in
# Class-based views for web interface
class SignUpView(CreateView):
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('login')
    template_name = 'registration/signup.html'

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Account created successfully. Please log in.')
        return response

# API ViewSets
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

# Function-based views for web interface
@login_required
def profile_view(request):
    return render(request, 'users/profile.html', {
        'user': request.user
    })

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
    
    return render(request, 'users/update_profile.html', {
        'form': form
    })

# Staff-only views
@login_required
def user_list(request):
    if not request.user.is_staff_user():
        messages.error(request, 'Access denied. Staff only.')
        return redirect('users:profile')
    
    users = User.objects.all()
    return render(request, 'users/user_list.html', {
        'users': users
    })