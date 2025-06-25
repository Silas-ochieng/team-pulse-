from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Q
from django.contrib.auth import get_user_model, logout
from .models import Attendance
import json
import openpyxl
from django.http import HttpResponse

User = get_user_model()

# Community-only: Check-in/out page
@login_required
def check_in_out_view(request):
    if not hasattr(request.user, "is_community_member") or not request.user.is_community_member():
        messages.error(request, "You do not have access to this page.")
        logout(request)
        return redirect('users:login')
    today = timezone.now().date()
    today_attendance = Attendance.objects.filter(
        user=request.user,
        date=today
    ).first()
    return render(request, 'attendance/attendance_form.html', {
        'today_attendance': today_attendance
    })

# Community-only: Check-in
@login_required
def check_in(request):
    if not hasattr(request.user, "is_community_member") or not request.user.is_community_member():
        messages.error(request, "You do not have access to this page.")
        logout(request)
        return redirect('users:login')
    if request.method == 'POST':
        today = timezone.now().date()
        if not Attendance.objects.filter(user=request.user, date=today).exists():
            Attendance.objects.create(user=request.user)
            messages.success(request, 'Checked in successfully!')
        else:
            messages.error(request, 'Already checked in today!')
    return redirect('attendance:check_in_out')

# Community-only: Check-out
@login_required
def check_out(request):
    if not hasattr(request.user, "is_community_member") or not request.user.is_community_member():
        messages.error(request, "You do not have access to this page.")
        logout(request)
        return redirect('users:login')
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

# Staff-only dashboard
@login_required
def dashboard(request):
    if not hasattr(request.user, "is_staff_user") or not request.user.is_staff_user():
        messages.error(request, "You do not have access to this page.")
        logout(request)
        return redirect('users:login')
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)

    # Today's stats
    today_attendance = Attendance.objects.filter(date=today)
    today_count = today_attendance.count()
    currently_present = today_attendance.filter(check_out__isnull=True).count()

    # Calculate late arrivals (e.g., after 9:30 AM)
    late_cutoff = timezone.datetime.combine(today, timezone.datetime.strptime('09:30', '%H:%M').time())
    late_count = today_attendance.filter(check_in__gt=late_cutoff).count()

    # Weekly stats
    weekly_stats = Attendance.objects.filter(
        date__gte=week_ago
    ).values('date').annotate(count=Count('id')).order_by('date')

    dates = [stat['date'].strftime('%a, %b %d') for stat in weekly_stats]
    counts = [stat['count'] for stat in weekly_stats]

    # Recent activity
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

# Staff-only: Export attendance to Excel
@login_required
def export_attendance_excel(request):
    if not hasattr(request.user, "is_staff_user") or not request.user.is_staff_user():
        messages.error(request, "You do not have access to this page.")
        logout(request)
        return redirect('users:login')

    user_query = request.GET.get('user', '')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    attendance_qs = Attendance.objects.all().select_related('user')

    if user_query:
        attendance_qs = attendance_qs.filter(
            Q(user__username__icontains=user_query) | Q(user__first_name__icontains=user_query) | Q(user__last_name__icontains=user_query)
        )
    if start_date:
        attendance_qs = attendance_qs.filter(date__gte=start_date)
    if end_date:
        attendance_qs = attendance_qs.filter(date__lte=end_date)

    # Create workbook & worksheet
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Attendance Records"

    # Write header
    headers = ['Username', 'Full Name', 'Date', 'Check-In Time', 'Check-Out Time']
    ws.append(headers)

    for att in attendance_qs.order_by('date'):
        ws.append([
            att.user.username,
            att.user.get_full_name(),
            att.date.strftime('%Y-%m-%d'),
            att.check_in.strftime('%H:%M:%S') if att.check_in else '',
            att.check_out.strftime('%H:%M:%S') if att.check_out else '',
        ])

    # Prepare response
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="attendance_records.xlsx"'
    wb.save(response)
    return response