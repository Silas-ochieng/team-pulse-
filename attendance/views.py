from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count
from .models import Attendance
from django.contrib.auth import get_user_model  # Add this import
import json

# Get the User model
User = get_user_model()  # Add this line

@login_required
def check_in_out_view(request):
    today = timezone.now().date()
    today_attendance = Attendance.objects.filter(
        user=request.user,
        date=today
    ).first()
    
    return render(request, 'attendance/attendance_form.html', {
        'today_attendance': today_attendance
    })

@login_required
def check_in(request):
    if request.method == 'POST':
        today = timezone.now().date()
        if not Attendance.objects.filter(user=request.user, date=today).exists():
            Attendance.objects.create(user=request.user)
            messages.success(request, 'Checked in successfully!')
        else:
            messages.error(request, 'Already checked in today!')
    return redirect('attendance:check_in_out')

@login_required
def check_out(request):
    if request.method == 'POST':
        today = timezone.now().date()
        try:
            attendance = Attendance.objects.get(
                user=request.user,
                date=today,
                check_out__isnull=True
            )
            attendance.check_out = timezone.now()
            attendance.save()
            messages.success(request, 'Checked out successfully!')
        except Attendance.DoesNotExist:
            messages.error(request, 'No active check-in found!')
    return redirect('attendance:check_in_out')

@user_passes_test(lambda u: u.is_authenticated and hasattr(u, 'is_staff_user') ) # Safer check
def dashboard(request):
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    
    # Today's stats
    today_attendance = Attendance.objects.filter(date=today)
    today_count = today_attendance.count()
    currently_present = today_attendance.filter(check_out__isnull=True).count()
    
    # Calculate late arrivals (example: after 9:30 AM)
    late_count = today_attendance.filter(
        check_in__time__gt=timezone.datetime.strptime('09:30', '%H:%M').time()
    ).count()
    
    # Weekly stats
    weekly_stats = Attendance.objects.filter(
        date__gte=week_ago
    ).values('date').annotate(count=Count('id')).order_by('date')
    
    dates = [stat['date'].strftime('%a, %b %d') for stat in weekly_stats]
    counts = [stat['count'] for stat in weekly_stats]
    
    # Recent attendance
    recent_attendance = Attendance.objects.select_related('user').order_by('-date')[:10]
    
    return render(request, 'attendance/dashboard.html', {
        'today_count': today_count,
        'currently_present': currently_present,
        'dates': json.dumps(dates),
        'counts': json.dumps(counts),
        'recent_attendance': recent_attendance,
        'pie_data': json.dumps([
            today_count - late_count,  # On time
            User.objects.count() - today_count,  # Absent
            late_count  # Late
        ])
    })