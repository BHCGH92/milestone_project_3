from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model() 

class TimeEntry(models.Model):
    ACTION_CHOICES = [
        ('IN', 'Clock In'),
        ('OUT', 'Clock Out'),
        ('BREAK_START', 'Start Break'),
        ('BREAK_END', 'End Break'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    timestamp = models.DateTimeField()
    action_type = models.CharField(max_length=12, choices=ACTION_CHOICES)
    
    
    date_only = models.DateField(db_index=True)

    def save(self, *args, **kwargs):
        
        if self.timestamp:
            self.date_only = self.timestamp.date()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} - {self.action_type} at {self.timestamp.strftime('%Y-%m-%d %H:%M')}"
    
    class Meta:
        verbose_name_plural = "Time Entries"

class TimeEditRequest(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending Approval'),
        ('ACCEPTED', 'Accepted'),
        ('REJECTED', 'Rejected'),
    ]

    original_entry = models.ForeignKey(
        TimeEntry, 
        on_delete=models.CASCADE, 
        related_name='edit_requests',
        help_text="The original TimeEntry record being requested for change."
    )
    requested_timestamp = models.DateTimeField(
        help_text="The new date and time the user wants the entry set to."
    )
    request_reason = models.TextField()
    
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    admin_reviewer = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='reviewed_edits'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Edit request for {self.original_entry.id} - Status: {self.status}"