from django import forms
from .models import TimeEntry

class AdminTimeEntryForm(forms.Form):
    # Use built-in model choices for validation and clarity
    ACTION_CHOICES = TimeEntry.ACTION_CHOICES 

    # Target user is hidden or handled by the view, but we need the data fields
    
    date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))
    time = forms.TimeField(widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}))
    action_type = forms.ChoiceField(choices=ACTION_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))

    class Meta:
        fields = ['date', 'time', 'action_type']