from django.urls import path
from . import views

app_name = 'patients'

urlpatterns = [
    # Dashboard
    path('dashboard/', views.patient_dashboard, name='dashboard'),
    
    # Profile Management
    path('profile/', views.patient_profile, name='profile'),
    path('profile/edit/', views.edit_patient_profile, name='edit_profile'),
    
    # Appointment Management
    path('appointments/', views.patient_appointments, name='appointments'),
    path('appointments/book/', views.book_appointment, name='book_appointment'),
    path('appointments/<int:appointment_id>/cancel/', views.cancel_appointment, name='cancel_appointment'),
    path('appointments/<int:appointment_id>/reschedule/', views.reschedule_appointment, name='reschedule_appointment'),
    
    # Medical History
    path('medical-history/', views.medical_history, name='medical_history'),
    path('medical-records/<int:record_id>/', views.medical_record_detail, name='medical_record_detail'),
    
    # Billing and Payments
    path('billing/', views.patient_billing, name='billing'),
    path('billing/<int:bill_id>/', views.bill_detail, name='bill_detail'),
    path('billing/<int:bill_id>/pay/', views.pay_bill, name='pay_bill'),
    
    # Health Education
    path('health-resources/', views.health_resources, name='health_resources'),
    path('health-resources/<int:resource_id>/', views.health_resource_detail, name='health_resource_detail'),
    
    # Prescriptions
    path('prescriptions/', views.patient_prescriptions, name='prescriptions'),
    path('prescriptions/<int:prescription_id>/', views.prescription_detail, name='prescription_detail'),
]
