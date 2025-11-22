from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect 
from django.contrib.auth.decorators import login_required 
from django.utils import timezone 
from .models import TimeEntry

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

@login_required
def reports_view(request):
    """
    Placeholder for the historical reports and date-range filtering.
    """
    context = {} 
    return render(request, 'time_tracker/reports.html', context)