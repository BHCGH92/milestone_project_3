from django import forms
from .models import TimeEntry
from .models import TimeEntry, TimeEditRequest
from django.utils import timezone


# --- 1. Admin Time Entry Form (Used for Manual Submission) ---
class AdminTimeEntryForm(forms.Form):
    date = forms.DateField(
        initial=timezone.localdate(),
        widget=forms.DateInput(attrs={'class': 'form-control'}))
        
    time = forms.TimeField(
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}))
        
    action_type = forms.ChoiceField(
        choices=TimeEntry.ACTION_CHOICES, 
        widget=forms.Select(attrs={'class': 'form-select form-control'}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class UserEditRequestForm(forms.ModelForm):
    original_entry = forms.ModelChoiceField(
        queryset=TimeEntry.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Select Entry to Modify'
    )
    requested_timestamp = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
        label='Requested New Time & Date', 
        initial=timezone.now(),
        required=True
    )
    
    class Meta:
        model = TimeEditRequest
        fields = ['original_entry', 'requested_timestamp', 'request_reason']
        widgets = {
            'request_reason': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'})
        }