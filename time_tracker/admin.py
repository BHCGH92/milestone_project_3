from django.contrib import admin
from .models import TimeEntry, TimeEditRequest
from django.utils.html import format_html 


#Added these classes to make sure my table views were clearer in the admin section

class TimeEntryAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'timestamp', 'action_display', 'date_only')
    list_filter = ('user', 'action_type', 'date_only')
    search_fields = ('user__username', 'action_type')
    def action_display(self, obj):
        color = 'green' if obj.action_type == 'IN' else ('red' if obj.action_type == 'OUT' else 'orange')
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', 
                           color, obj.get_action_type_display())
    action_display.short_description = 'Action'

class TimeEditRequestAdmin(admin.ModelAdmin):

    list_display = ('id', 'original_entry', 'requested_timestamp', 'status', 'admin_reviewer', 'reviewed_at')
    
    list_filter = ('status', 'admin_reviewer', 'reviewed_at')

    search_fields = ('original_entry__user__username', 'request_reason')

    readonly_fields = ['original_entry', 'requested_timestamp', 'request_reason']

admin.site.register(TimeEntry, TimeEntryAdmin) 
admin.site.register(TimeEditRequest, TimeEditRequestAdmin)