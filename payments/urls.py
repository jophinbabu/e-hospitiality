from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    # Payment initiation
    path('appointment/<int:appointment_id>/', views.initiate_payment, name='appointment_payment'),
    path('doctor/<int:doctor_id>/', views.initiate_payment, name='doctor_payment'),
    
    # Payment processing
    path('success/', views.payment_success, name='success'),
    path('failed/', views.payment_failed, name='failed'),
    
    # Payment history
    path('history/', views.payment_history, name='history'),
]
