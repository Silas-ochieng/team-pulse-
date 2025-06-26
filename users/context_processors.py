# users/context_processors.py
from .models import CustomUser

def pending_approvals_count(request):
    if request.user.is_superuser:
        return {
            'pending_approvals_count': CustomUser.objects.filter(
                user_type='staff', 
                is_approved=False
            ).count()
        }
    return {}