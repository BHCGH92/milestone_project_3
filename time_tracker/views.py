from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect 
from django.contrib.auth.decorators import login_required 
from django.utils import timezone 
from .models import TimeEntry, TimeEditRequest
from datetime import date, timedelta
from .utils import calculate_time_period
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.contrib.auth.views import LoginView
from urllib.parse import urlencode
from django.urls import reverse
from datetime import datetime
from .forms import AdminTimeEntryForm, UserEditRequestForm
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction

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

    pending_request_count = 0
    if request.user.is_staff:
        pending_request_count = TimeEditRequest.objects.filter(status='PENDING').count()

    context = {
        'current_status': user_status, 
        'hours_today': results['work_duration'], 
        'raw_logs_today': page_obj, # <--- Passing the paginated object
        'pending_request_count': pending_request_count,
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

@login_required
def admin_delete_entry(request, entry_id):
    if not request.user.is_staff:
        raise PermissionDenied
    
    entry = get_object_or_404(TimeEntry, id=entry_id)
    
    if request.method == 'POST':
        entry.delete()
        messages.success(request, f"Entry {entry_id} for {entry.user.username} deleted.")
        return redirect('admin_user_management') 
        
    messages.warning(request, "Deletion requires POST method.")
    return redirect('admin_user_management')

@login_required
def admin_user_management(request):
    if not request.user.is_staff:
        raise PermissionDenied

    target_user = None
    user_id = request.GET.get('user_id')
    
    add_form = AdminTimeEntryForm() 
    
    # --- POST LOGIC ---
    if request.method == 'POST':
        user_id = request.POST.get('target_user_id')
        role_action = request.POST.get('role_action') 
        
        if not user_id:
             messages.error(request, "Target user ID is missing from the submission.")
             return redirect('admin_user_management')
        
        target_user_to_update = get_object_or_404(User, id=user_id)
        
        if role_action == 'toggle_staff':
            # Handle Role Toggle
            target_user_to_update.is_staff = not target_user_to_update.is_staff
            target_user_to_update.save()
            messages.success(request, f"User {target_user_to_update.username} staff status updated.")
            return redirect(f"{reverse('admin_user_management')}?user_id={user_id}")
            
    
        if 'date' in request.POST:
            add_form = AdminTimeEntryForm(request.POST) 
            
            if add_form.is_valid():
                entry_date = add_form.cleaned_data['date']
                entry_time = add_form.cleaned_data['time']
                action_type = add_form.cleaned_data['action_type']
                
                entry_datetime = timezone.make_aware(datetime.combine(entry_date, entry_time))
                
                TimeEntry.objects.create(
                    user=target_user_to_update,
                    timestamp=entry_datetime,
                    action_type=action_type
                )
                messages.success(request, f"Entry added for {target_user_to_update.username} on {entry_date}.")
                return redirect(f"{reverse('admin_user_management')}?user_id={user_id}")
            
        else:
            messages.error(request, "Invalid form submission detected.")
            return redirect(f"{reverse('admin_user_management')}?user_id={user_id}")


    user_entries = None
    query_params = ""
    
    add_form = AdminTimeEntryForm() 
    
    for field_name in add_form.fields:
        add_form.fields[field_name].widget.attrs.update({
            'class': 'form-control'
        })
    
    user_id = request.GET.get('user_id')
    if not user_id:
        first_user = User.objects.all().order_by('id').first()
        if first_user:
            user_id = str(first_user.id)
        else:
            user_id = str(request.user.id) 

    if user_id:
        target_user = get_object_or_404(User, id=user_id)
        
        all_user_entries = TimeEntry.objects.filter(user=target_user).order_by('-timestamp')
        
        PAGINATE_BY = 15 
        paginator = Paginator(all_user_entries, PAGINATE_BY)
        page_number = request.GET.get('page')
        user_entries = paginator.get_page(page_number) 
        
        query_params = urlencode({'user_id': target_user.id})
        
    context = {
        'all_users': User.objects.all().order_by('username'),
        'target_user': target_user,
        'user_entries': user_entries,
        'query_params': query_params,
        'add_form': add_form,
    }
    return render(request, 'time_tracker/admin_management.html', context)

@login_required
def request_time_edit(request):
    if request.method == 'POST':
        form = UserEditRequestForm(request.POST)
        
        if form.is_valid():
            edit_request = form.save(commit=False)
            edit_request.user = request.user
            edit_request.status = 'PENDING'
            edit_request.save()
            messages.success(request, 'Time change request submitted successfully for review.')
            return redirect('dashboard')
    else:
        form = UserEditRequestForm()
        form.fields['original_entry'].queryset = TimeEntry.objects.filter(user=request.user).order_by('-timestamp')

    context = {'form': form}
    return render(request, 'time_tracker/user_edit_request.html', context)

MGMT_PAGINATE_BY = 15

@login_required
def admin_review_requests(request):
    if not request.user.is_staff:
        raise PermissionDenied
        
    # Fetch all PENDING requests
    all_requests = TimeEditRequest.objects.filter(status='PENDING').order_by('requested_timestamp')
    
    paginator = Paginator(all_requests, MGMT_PAGINATE_BY)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'pending_requests': page_obj,
    }
    return render(request, 'time_tracker/admin_review_requests.html', context)

@login_required
def admin_process_request(request, request_id):
    if not request.user.is_staff:
        raise PermissionDenied
        
    edit_request = get_object_or_404(TimeEditRequest, id=request_id)
    action = request.POST.get('action')
    
    if request.method == 'POST':
        if action == 'accept':
            with transaction.atomic():
                original_entry = edit_request.original_entry
                original_entry.timestamp = edit_request.requested_timestamp
                original_entry.save()
                
                edit_request.status = 'ACCEPTED'
                edit_request.admin_reviewer = request.user
                edit_request.reviewed_at = timezone.now()
                edit_request.save()
                
            messages.success(request, f"Entry {original_entry.id} accepted and updated.")
            
        elif action == 'reject':
            edit_request.status = 'REJECTED'
            edit_request.admin_reviewer = request.user
            edit_request.reviewed_at = timezone.now()
            edit_request.save()
            messages.warning(request, f"Entry {edit_request.original_entry.id} rejected.")

    return redirect('admin_review_requests')