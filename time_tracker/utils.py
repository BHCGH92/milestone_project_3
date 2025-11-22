# time_tracker/utils.py
from datetime import timedelta
from time_tracker.models import TimeEntry

def calculate_time_period(user, start_date, end_date):
    """
    Calculates total work and break time for a given user within a date range,
    returning durations as a float rounded to two decimal places (hours). Processing for payroll is easier this way.
    """
    entries = TimeEntry.objects.filter(
        user=user, 
        date_only__range=(start_date, end_date)
    ).order_by('timestamp')

    total_work_time = timedelta()
    total_break_time = timedelta()
    
    clock_in_time = None
    break_start_time = None
    
    # 1. Iterate and pair entries
    for entry in entries:
        # State transitions based on the entry action_type
        
        if entry.action_type == 'IN':
            clock_in_time = entry.timestamp
            
        elif entry.action_type == 'OUT' and clock_in_time:
            total_work_time += (entry.timestamp - clock_in_time)
            clock_in_time = None # Shift ended

        elif entry.action_type == 'BREAK_START' and clock_in_time:
            # When break starts, subtract the time worked SO FAR from the total_work_time, 
            # and pause the clock_in_time.
            total_work_time -= (entry.timestamp - clock_in_time)
            break_start_time = entry.timestamp
            
        elif entry.action_type == 'BREAK_END' and break_start_time:
            # When break ends, calculate break duration and add it to total_break_time.
            total_break_time += (entry.timestamp - break_start_time)
            break_start_time = None # Break ended
            # IMPORTANT: Re-start the clock_in_time at the end of the break to measure subsequent work
            clock_in_time = entry.timestamp 
            
    # --- CONVERSION TO DECIMAL HOURS ---
    
    # Convert timedelta to total seconds
    work_seconds = total_work_time.total_seconds()
    break_seconds = total_break_time.total_seconds()

    # Convert to hours (dividing by 3600) and round to two decimal places
    work_hours_decimal = round(work_seconds / 3600, 2)
    break_hours_decimal = round(break_seconds / 3600, 2)

    # 2. Return results
    return {
        'work_duration': work_hours_decimal,
        'break_duration': break_hours_decimal,
        'raw_entries': entries
    }