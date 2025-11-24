from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect 
from django.contrib.auth.decorators import login_required 
from django.utils import timezone 
from .models import TimeEntry
from datetime import date, timedelta
from .utils import calculate_time_period
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.contrib.auth.views import LoginView
from urllib.parse import urlencode

def custom_login(request):
    """If user is authenticated, redirect them to dashboard. Otherwise, display the login form."""
    if request.user.is_authenticated:
        # User is logged in, redirect them to the dashboard
        return redirect('dashboard')
    else:
        # User is NOT logged in, render the standard login page
        # We call the LoginView's logic directly, ensuring the context is correct.
        return LoginView.as_view(template_name='registration/login.html')(request)

def get_user_status(user):
    """
    Retrieves the action_type of the user's single most recent time entry 
    and translates 'BREAK_END' into 'IN'.
    """
    last_entry = TimeEntry.objects.filter(user=user).order_by('-timestamp').first()

    if not last_entry:
        return 'OUT'  # Default state if no entries exist
    
    # --- CRITICAL NEW LOGIC ---
    last_action = last_entry.action_type
    
    if last_action == 'BREAK_END':
        return 'IN' # User is back from break and actively working
    
    return last_action

@login_required
def dashboard(request):
    user_status = get_user_status(request.user)
    today = timezone.localdate()
    
    # Calculate totals using ALL entries for the day (Logic remains separate)
    results = calculate_time_period(request.user, today, today) 

    # --- PAGINATION LOGIC START ---
    
    # 1. Fetch all raw entries for today (QuerySet)
    today = timezone.localdate()
    all_entries_today = TimeEntry.objects.filter(
    user=request.user,
    date_only=today
    ).order_by('-timestamp')

    # 2. Set up Paginator
    PAGINATE_BY = 10 
    paginator = Paginator(all_entries_today, PAGINATE_BY)

    # 3. Get the requested page number from the URL (?page=X)
    page_number = request.GET.get('page')
    
    # 4. Get the specific page object (the slice of data)
    page_obj = paginator.get_page(page_number) 
    
    # --- PAGINATION LOGIC END ---

    context = {
        'current_status': user_status, 
        'hours_today': results['work_duration'], 
        'raw_logs_today': page_obj, # <--- Passing the paginated object
    }
    return render(request, 'time_tracker/dashboard.html', context)

@login_required
def clock_action(request):
    if request.method == 'POST':
        action_type = request.POST.get('action') 
        user_status = get_user_status(request.user) 
        
        is_valid = False
        
            # 1. CLOCK IN: Only allowed if user is currently OUT.
        if action_type == 'IN' and user_status == 'OUT': # <-- SIMPLIFIED: Only allow 'OUT'
            is_valid = True
            
        # 2. CLOCK OUT: Allowed if user is currently IN or on a BREAK
        elif action_type == 'OUT' and user_status in ['IN', 'BREAK_START']: # <-- REMOVE 'BREAK_END' here
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
    today = timezone.localdate()
    default_start_date = today - timedelta(days=7)
    date_from_str = request.GET.get('date_from')
    date_to_str = request.GET.get('date_to')
    user_id_str = request.GET.get('user_id')

    target_user = request.user
    
    if request.user.is_staff and user_id_str:
        try:
            target_user = User.objects.get(id=user_id_str)
        except User.DoesNotExist:
            pass

    try:
        date_from = date.fromisoformat(date_from_str) if date_from_str else default_start_date
        date_to = date.fromisoformat(date_to_str) if date_to_str else today
    except ValueError:
        date_from = default_start_date
        date_to = today

    if date_to < date_from:
        date_to = date_from
    
    results = calculate_time_period(target_user, date_from, date_to)

    all_report_entries = results['raw_entries'] 
    
    PAGINATE_BY = 10 
    paginator = Paginator(all_report_entries, PAGINATE_BY)

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number) 
    
    query_params_dict = {
        'date_from': date_from.isoformat(),
        'date_to': date_to.isoformat(),
    }
    if request.user.is_staff and target_user.id != request.user.id:
        query_params_dict['user_id'] = target_user.id
        
    query_params = urlencode(query_params_dict)

    context = {
        'date_from': date_from.isoformat(), 
        'date_to': date_to.isoformat(),
        'target_user': target_user,
        'is_admin': request.user.is_staff,
        'users': User.objects.all().order_by('username') if request.user.is_staff else None,
        'total_work_time': results['work_duration'],
        'total_break_time': results['break_duration'],
        'raw_entries': page_obj, 
        'query_params': query_params,
    }
    return render(request, 'time_tracker/reports.html', context)

def register_user(request):
    """Handles user registration (sign-up)."""
    if request.method == 'POST':
        # If the form is submitted (POST request)
        form = UserCreationForm(request.POST)
        if form.is_valid():
            # Save the new user and hash the password
            user = form.save() 
            # Send a success message
            messages.success(request, f'Account created for {user.username}. You can now log in.')
            # Redirect to the login page
            return redirect('login') 
    else:
        # If the page is just being loaded (GET request)
        form = UserCreationForm()
        
    context = {'form': form}
    return render(request, 'registration/register.html', context)