from django.urls import path
from . import views

app_name = 'doctors'

urlpatterns = [
    path('dashboard/', views.doctor_dashboard, name='dashboard'),
    path('appointments/', views.doctor_appointments, name='appointments'),
    path('appointments/create/', views.create_appointment, name='create_appointment'),  # Added this line
    path('patients/', views.doctor_patients, name='patients'),
    path('prescriptions/', views.doctor_prescriptions, name='prescriptions'),
    path('schedule/', views.doctor_schedule, name='schedule'),
    path('profile/', views.doctor_profile, name='profile'),
    
    # Appointment management
    path('appointment/<int:appointment_id>/', views.appointment_detail, name='appointment_detail'),
    path('appointment/<int:appointment_id>/complete/', views.complete_appointment, name='complete_appointment'),
    path('appointment/<int:appointment_id>/cancel/', views.cancel_appointment, name='cancel_appointment'),  # Added this
    
    # Patient management
    path('patient/<int:patient_id>/', views.patient_detail, name='patient_detail'),
    
    # Prescription management
    path('prescription/create/', views.create_prescription, name='create_prescription'),
    path('prescription/create/<int:patient_id>/', views.create_prescription, name='create_prescription_for_patient'),
    path('prescription/<int:prescription_id>/', views.prescription_detail, name='prescription_detail'),
    
    # Additional features
    path('availability/', views.set_availability, name='set_availability'),
    path('medical-records/', views.medical_records, name='medical_records'),
]
