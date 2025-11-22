from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect 
from django.contrib.auth.decorators import login_required 
from django.utils import timezone 
from .models import TimeEntry
from datetime import date, timedelta
from .utils import calculate_time_period
from django.contrib.auth import get_user_model

def get_user_status(user):
    """
    Retrieves the action_type of the user's most recent time entry.
    This defines the user's current status (IN, OUT, BREAK_START etc.).
    """
    # 1. Filters entries for the current user.
    # 2. Orders them by timestamp in descending order (newest first).
    # 3. .first() retrieves only the single, most recent entry.
    last_entry = TimeEntry.objects.filter(user=user).order_by('-timestamp').first()

    # If the user has no entries, out will be the default
    if not last_entry:
        return 'OUT'
    
    # If it's not out, it will be the last status that was used.
    return last_entry.action_type

@login_required
def dashboard(request):
    
    user_status = get_user_status(request.user) 
    
    #This will be expanded in later commits
    context = {
        'current_status': user_status, 
        'hours_today': '0.00' # using placeholder for now
    }
    return render(request, 'time_tracker/dashboard.html', context)

@login_required
def clock_action(request):

    """
    Handles POST requests from clocking buttons and enforces business rules.
    """
    if request.method == 'POST':
        action_type = request.POST.get('action') 
        user_status = get_user_status(request.user)
        
        is_valid = False
        
        # --- Business Logic Validation ---
        
        # 1. CLOCK IN: Allowed if user is currently OUT or has ended a break
        if action_type == 'IN' and user_status in ['OUT', 'BREAK_END']:
            is_valid = True
            
        # 2. CLOCK OUT: Allowed if user is currently IN or on a break.
        elif action_type == 'OUT' and user_status in ['IN', 'BREAK_START', 'BREAK_END']:
            is_valid = True
            
        # 3. START BREAK: Allowed only if user is IN
        elif action_type == 'BREAK_START' and user_status == 'IN':
            is_valid = True
            
        # 4. END BREAK: Allowed only if user is on a BREAK_START
        elif action_type == 'BREAK_END' and user_status == 'BREAK_START':
            is_valid = True
            
        if is_valid:
            # This creates the new entry in the database
            TimeEntry.objects.create(
                user=request.user,
                timestamp=timezone.now(),
                action_type=action_type
            )

    # Redirects user back to the dashboard
    return redirect('dashboard')

User = get_user_model() 

@login_required



def reports_view(request):
    # Set default date range to the last 7 days ending today
    today = timezone.localdate()
    default_start_date = today - timedelta(days=7)
    date_from_str = request.GET.get('date_from')
    date_to_str = request.GET.get('date_to')
    user_id_str = request.GET.get('user_id') # For Admin report filtering

    # --- 1. Define User (Who is the report for?) ---
    target_user = request.user
    
    # Allow Admins to select any user
    if request.user.is_staff and user_id_str:
        try:
            target_user = User.objects.get(id=user_id_str)
        except User.DoesNotExist:
            pass # Default to current user if requested user is not found

    # --- 2. Define Date Range ---
    try:
        # Parse dates from the form input, or use the default range
        date_from = date.fromisoformat(date_from_str) if date_from_str else default_start_date
        date_to = date.fromisoformat(date_to_str) if date_to_str else today
    except ValueError:
        # Fallback if date format is invalid
        date_from = default_start_date
        date_to = today

    # Ensure date_to is not before date_from
    if date_to < date_from:
        date_to = date_from
    
    # --- 3. Calculate Report Data ---
    # Call the calculation utility with the determined user and date range
    results = calculate_time_period(target_user, date_from, date_to)

    context = {
        'date_from': date_from.isoformat(), # Used to pre-fill the form fields
        'date_to': date_to.isoformat(),     # Used to pre-fill the form fields
        'target_user': target_user,
        'is_admin': request.user.is_staff,
        'users': User.objects.all().order_by('username') if request.user.is_staff else None,
        'total_work_time': results['work_duration'],
        'total_break_time': results['break_duration'],
        'raw_entries': results['raw_entries'], # Raw data for detailed breakdown
    }
    return render(request, 'time_tracker/reports.html', context)

@login_required
def dashboard(request):
    user_status = get_user_status(request.user)
    
    # --- Integration Start ---
    today = timezone.localdate() # Get today's date
    
    # We pass the same date for start and end to calculate today's hours
    results = calculate_time_period(request.user, today, today) 
    
    # --- Integration End ---
    
    context = {
        'current_status': user_status, 
        'hours_today': results['work_duration'], 
        'raw_logs_today': results['raw_entries']
    }
    return render(request, 'time_tracker/dashboard.html', context)