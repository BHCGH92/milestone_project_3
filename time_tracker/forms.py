from django import forms
from .models import TimeEntry
from .models import TimeEntry, TimeEditRequest

class AdminTimeEntryForm(forms.Form):
    # Use built-in model choices for validation and clarity
    ACTION_CHOICES = TimeEntry.ACTION_CHOICES 

    # Target user is hidden or handled by the view, but we need the data fields
    
    date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))
    time = forms.TimeField(widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}))
    action_type = forms.ChoiceField(choices=ACTION_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))

    class Meta:
        fields = ['date', 'time', 'action_type']


class AdminTimeEntryForm(forms.Form):
    pass

class UserEditRequestForm(forms.ModelForm):
    original_entry = forms.ModelChoiceField(
        queryset=TimeEntry.objects.all(), 
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Select Entry to Modify'
    )
    
    requested_timestamp = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
        label='Requested Date & Time (New Value)'
    )
    
    class Meta:
        model = TimeEditRequest
        fields = ['original_entry', 'requested_timestamp', 'request_reason']
        widgets = {
            'request_reason': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'})
        }