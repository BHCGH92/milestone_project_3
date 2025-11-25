# time_tracker/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('clock/', views.clock_action, name='clock_action'),
    path('reports/', views.reports_view, name='reports'),
    path('register/', views.register_user, name='register'),
    path('manageusers', views.admin_user_management, name='admin_user_management'),
    path('delete/<int:entry_id>/', views.admin_delete_entry, name='admin_delete_entry'),
    path('request/edit/', views.request_time_edit, name='request_time_edit'),
    path('manage/requests/', views.admin_review_requests, name='admin_review_requests'),
    path('manage/requests/<int:request_id>/process/', views.admin_process_request, name='admin_process_request'),
]