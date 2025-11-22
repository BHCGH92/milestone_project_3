# time_tracker/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('clock/', views.clock_action, name='clock_action'),
    path('reports/', views.reports_view, name='reports'),
]