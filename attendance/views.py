from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta, datetime
from django.db.models import Count, Q
from django.contrib.auth import get_user_model
from .models import Attendance
import json
import openpyxl
from django.http import HttpResponse
from django.core.cache import cache

User = get_user_model()

def validate_date(date_str, default_date):
    """Helper function to validate and parse date strings"""
    if not date_str:
        return default_date
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return default_date

def community_or_staff_required(view_func):
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if not (request.user.is_community_member() or request.user.is_staff_user()):
            messages.error(request, "Access denied")
            return redirect('users:profile')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

@login_required
def check_in_out_view(request):
    if not (request.user.is_staff_user or request.user.is_community_member or request.user.is_superuser):
        messages.error(request, "Access denied")
        return redirect('users:profile')
    
    today = timezone.now().date()
    today_attendance = Attendance.objects.filter(
        user=request.user,
        date=today
    ).first()
    
    return render(request, 'attendance/attendance_form.html', {
        'today_attendance': today_attendance,
        'current_user_type': request.user.user_type
    })

@login_required
def check_in(request):
    if not (request.user.is_staff_user or request.user.is_community_member or request.user.is_superuser):
        messages.error(request, "Access denied")
        return redirect('users:profile')
    
    if request.method == 'POST':
        today = timezone.now().date()
        if not Attendance.objects.filter(user=request.user, date=today).exists():
            Attendance.objects.create(user=request.user)
            messages.success(request, 'Checked in successfully!')
            cache.delete('dashboard_stats')
        else:
            messages.error(request, 'Already checked in today!')
    
    return redirect('attendance:check_in_out')

@login_required
def check_out(request):
    if not (request.user.is_staff_user or request.user.is_community_member or request.user.is_superuser):
        messages.error(request, "Access denied")
        return redirect('users:profile')
    
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
            cache.delete('dashboard_stats')
        except Attendance.DoesNotExist:
            messages.error(request, 'No active check-in found!')
    
    return redirect('attendance:check_in_out')

@login_required
def dashboard(request):
    if not (request.user.is_staff_user or request.user.is_superuser):
        messages.error(request, "Staff access required")
        return render(request, 'attendance/dashboard.html', {
            'error': "You do not have permission to view this page.",
            'show_profile_links': request.user.is_staff_user()
        })

    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    
    # Get and validate date parameters
    start_date = validate_date(request.GET.get('start_date'), week_ago)
    end_date = validate_date(request.GET.get('end_date'), today)
    
    # Ensure date range is valid
    if end_date < start_date:
        end_date = start_date
        messages.warning(request, "End date was adjusted to match start date")
    
    user_type = request.GET.get('user_type', 'all')
    user_id = request.GET.get('user_id')
    
    all_users = User.objects.filter(
        Q(user_type='staff') | Q(user_type='community')
    ).order_by('first_name')
    
    attendance_qs = Attendance.objects.filter(
        date__range=[start_date, end_date]
    ).select_related('user')
    
    if user_type == 'staff':
        attendance_qs = attendance_qs.filter(user__user_type='staff')
    elif user_type == 'community':
        attendance_qs = attendance_qs.filter(user__user_type='community')
    
    if user_id:
        attendance_qs = attendance_qs.filter(user_id=user_id)
        selected_user = get_object_or_404(User, id=user_id)
        messages.info(request, f"Showing data for {selected_user.get_full_name()}")
    
    # Today's stats with proper null handling
    today_stats = attendance_qs.filter(date=today).aggregate(
        total=Count('id'),
        present=Count('id', filter=Q(check_out__isnull=True)),
        late=Count('id', filter=Q(check_in__gt=timezone.datetime.combine(
            today, timezone.datetime.strptime('09:30', '%H:%M').time()
        )))
    )
    
    # Weekly stats with user type differentiation
    weekly_stats = attendance_qs.filter(
        date__gte=week_ago
    ).values('date', 'user__user_type').annotate(count=Count('id')).order_by('date')
    
    # Prepare data for charts - ensure we have data for all days in the range
    date_range = [start_date + timedelta(days=x) for x in range((end_date - start_date).days + 1)]
    date_labels = [date.strftime('%a, %b %d') for date in date_range]
    
    # Initialize with zeros
    staff_counts = {date: 0 for date in date_labels}
    community_counts = {date: 0 for date in date_labels}
    user_details = {date: "No data" for date in date_labels}
    
    # Populate with actual data
    for stat in weekly_stats:
        date_str = stat['date'].strftime('%a, %b %d')
        if stat['user__user_type'] == 'staff':
            staff_counts[date_str] = stat['count']
        elif stat['user__user_type'] == 'community':
            community_counts[date_str] = stat['count']
        
        # Build user details string
        details = f"{stat['user__user_type'].capitalize()}: {stat['count']}"
        if user_details[date_str] == "No data":
            user_details[date_str] = details
        else:
            user_details[date_str] += f", {details}"
    
    # Convert to lists in correct order
    staff_counts_list = [staff_counts[date] for date in date_labels]
    community_counts_list = [community_counts[date] for date in date_labels]
    user_details_list = [user_details[date] for date in date_labels]
    
    # Recent activity
    recent_attendance = attendance_qs.select_related('user').order_by('-date')[:10]
    
    # User type breakdown for today
    today_breakdown = attendance_qs.filter(date=today).values(
        'user__user_type'
    ).annotate(count=Count('id')).order_by('user__user_type')
    
    staff_count = next((t['count'] for t in today_breakdown if t['user__user_type'] == 'staff'), 0)
    community_count = next((t['count'] for t in today_breakdown if t['user__user_type'] == 'community'), 0)
    
    total_users = User.objects.filter(Q(user_type='staff') | Q(user_type='community')).count()
    today_total = today_stats.get('total', 0) or 0
    late_count = today_stats.get('late', 0) or 0
    on_time_count = today_total - late_count
    absent_count = total_users - today_total

    context = {
        'today_count': today_total,
        'currently_present': today_stats.get('present', 0) or 0,
        'late_count': late_count,
        'staff_count': staff_count,
        'community_count': community_count,
        'dates': json.dumps(date_labels),
        'staff_counts': json.dumps(staff_counts_list),
        'community_counts': json.dumps(community_counts_list),
        'recent_attendance': recent_attendance,
        'all_users': all_users,
        'user_type_filter': user_type,
        'start_date': start_date.isoformat(),
        'end_date': end_date.isoformat(),
        'pie_data': json.dumps([on_time_count, absent_count, late_count]),
        'total_users': total_users,
        'on_time_count': on_time_count,
        'absent_count': absent_count,
        'user_details': json.dumps(user_details_list),
        'show_profile_links': request.user.is_staff_user()
    }

    return render(request, 'attendance/dashboard.html', context)

@login_required
def export_attendance_excel(request):
    if not request.user.is_staff_user():
        messages.error(request, "Staff access required")
        return redirect('users:profile')
    
    user_type = request.GET.get('user_type', 'all')
    user_id = request.GET.get('user_id')
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    
    # Validate dates for export
    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date() if start_date_str else None
    except (ValueError, TypeError):
        start_date = None
    
    try:
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date() if end_date_str else None
    except (ValueError, TypeError):
        end_date = None
    
    attendance_qs = Attendance.objects.all().select_related('user')
    
    if user_type == 'staff':
        attendance_qs = attendance_qs.filter(user__user_type='staff')
    elif user_type == 'community':
        attendance_qs = attendance_qs.filter(user__user_type='community')
    
    if user_id:
        attendance_qs = attendance_qs.filter(user_id=user_id)
    
    if start_date:
        attendance_qs = attendance_qs.filter(date__gte=start_date)
    
    if end_date:
        attendance_qs = attendance_qs.filter(date__lte=end_date)
    
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Attendance Records"
    
    headers = [
        'Username', 
        'Full Name', 
        'User Type',
        'Date', 
        'Check-In Time', 
        'Check-Out Time',
        'Hours Worked'
    ]
    ws.append(headers)
    
    for att in attendance_qs.order_by('date', 'user__last_name'):
        check_in_time = att.check_in.time() if att.check_in else None
        check_out_time = att.check_out.time() if att.check_out else None
        
        hours_worked = 0
        if att.check_in and att.check_out:
            delta = att.check_out - att.check_in
            hours_worked = round(delta.total_seconds() / 3600, 2)
        
        ws.append([
            att.user.username,
            att.user.get_full_name(),
            att.user.get_user_type_display(),
            att.date.strftime('%Y-%m-%d'),
            check_in_time.strftime('%H:%M:%S') if check_in_time else '',
            check_out_time.strftime('%H:%M:%S') if check_out_time else '',
            hours_worked
        ])
    
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="attendance_records.xlsx"'
    wb.save(response)
    
    return response