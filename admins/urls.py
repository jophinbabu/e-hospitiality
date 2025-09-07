from django.urls import path
from . import views

app_name = 'admins'

urlpatterns = [
    path('dashboard/', views.admin_dashboard, name='dashboard'),
    path('users/', views.user_management, name='user_management'),
    path('appointments/', views.appointment_management, name='appointment_management'),
    path('billing/', views.billing_management, name='billing_management'),
    path('reports/', views.reports, name='reports'),
    path('settings/', views.system_settings, name='system_settings'),
]
