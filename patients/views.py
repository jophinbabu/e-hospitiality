from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.core.paginator import Paginator
from .models import Patient, MedicalRecord, Billing

# Import models conditionally to avoid circular imports
try:
    from doctors.models import Doctor, Prescription
    from core.models import Appointment, Department
except ImportError:
    Doctor = None
    Prescription = None
    Appointment = None
    Department = None

def patient_required(view_func):
    """Decorator to ensure only patients can access the view"""
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.user_type != 'patient':
            messages.error(request, 'Access denied. Patients only.')
            return redirect('core:home')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

@login_required
@patient_required
def patient_dashboard(request):
    """Patient dashboard view"""
    try:
        patient = Patient.objects.get(user=request.user)
    except Patient.DoesNotExist:
        # Create patient profile if it doesn't exist
        patient = Patient.objects.create(
            user=request.user,
            patient_id=f"P{request.user.id:06d}"
        )
    
    # Get appointments queryset (don't slice yet)
    if Appointment:
        appointments_queryset = Appointment.objects.filter(
            patient=patient
        ).order_by('-appointment_date')
        
        # Get recent appointments (slice here)
        recent_appointments = appointments_queryset[:5]
        
        # Get next appointment (filter before any slicing)
        next_appointment = appointments_queryset.filter(
            appointment_date__gte=timezone.now(),
            status='scheduled'
        ).first()
    else:
        recent_appointments = []
        next_appointment = None
    
    # Get other dashboard data
    try:
        recent_records = MedicalRecord.objects.filter(
            patient=patient
        ).order_by('-date_created')[:3]
    except:
        recent_records = []
    
    try:
        recent_prescriptions = Prescription.objects.filter(
            patient=patient
        ).order_by('-created_at')[:3] if Prescription else []
    except:
        recent_prescriptions = []
    
    try:
        unpaid_bills = Billing.objects.filter(
            patient=patient, 
            is_paid=False
        ).order_by('-created_at')
    except:
        unpaid_bills = []
    
    context = {
        'patient': patient,
        'recent_appointments': recent_appointments,
        'unpaid_bills': unpaid_bills,
        'recent_records': recent_records,
        'recent_prescriptions': recent_prescriptions,
        'total_bills': unpaid_bills.count() if unpaid_bills else 0,
        'next_appointment': next_appointment,
    }
    return render(request, 'patients/dashboard.html', context)

@login_required
@patient_required
def patient_profile(request):
    """Patient profile view"""
    patient = get_object_or_404(Patient, user=request.user)
    
    if request.method == 'POST':
        # Update patient information
        patient.emergency_contact = request.POST.get('emergency_contact', patient.emergency_contact)
        patient.blood_group = request.POST.get('blood_group', patient.blood_group)
        patient.allergies = request.POST.get('allergies', patient.allergies)
        patient.medical_history = request.POST.get('medical_history', patient.medical_history)
        patient.save()
        
        # Update user information
        user = patient.user
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        user.phone = request.POST.get('phone', user.phone)
        user.address = request.POST.get('address', user.address)
        user.save()
        
        messages.success(request, 'Profile updated successfully!')
        return redirect('patients:profile')
    
    return render(request, 'patients/profile.html', {'patient': patient})

@login_required
@patient_required
def patient_appointments(request):
    """View all patient appointments"""
    patient = get_object_or_404(Patient, user=request.user)
    
    if Appointment:
        appointments = Appointment.objects.filter(patient=patient).order_by('-appointment_date')
    else:
        appointments = []
    
    paginator = Paginator(appointments, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'appointments': page_obj,
        'patient': patient,
    }
    return render(request, 'patients/appointments.html', context)

@login_required
@patient_required
def book_appointment(request):
    """Book new appointment"""
    patient = get_object_or_404(Patient, user=request.user)
    
    if request.method == 'POST':
        doctor_id = request.POST.get('doctor')
        appointment_date = request.POST.get('appointment_date')
        reason = request.POST.get('reason')
        
        if doctor_id and appointment_date and reason:
            try:
                if Doctor:
                    doctor = Doctor.objects.get(id=doctor_id)
                    
                    if Appointment:
                        appointment = Appointment.objects.create(
                            patient=patient,
                            doctor=doctor,
                            appointment_date=appointment_date,
                            reason=reason,
                            status='scheduled'
                        )
                        
                        messages.success(request, 'Appointment booked successfully!')
                        return redirect('patients:appointments')
                    else:
                        messages.error(request, 'Appointment system not available.')
                else:
                    messages.error(request, 'Doctor system not available.')
            except Exception as e:
                messages.error(request, f'Error booking appointment: {str(e)}')
        else:
            messages.error(request, 'Please fill in all required fields.')
    
    doctors = Doctor.objects.filter(is_available=True) if Doctor else []
    departments = Department.objects.all() if Department else []
    
    context = {
        'doctors': doctors,
        'departments': departments,
        'patient': patient,
        'today': timezone.now().strftime('%Y-%m-%d'),
    }
    return render(request, 'patients/book_appointment.html', context)

@login_required
@patient_required
def medical_history(request):
    """View medical history"""
    patient = get_object_or_404(Patient, user=request.user)
    medical_records = MedicalRecord.objects.filter(patient=patient).order_by('-date_created')
    
    paginator = Paginator(medical_records, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'medical_records': page_obj,
        'patient': patient,
    }
    return render(request, 'patients/medical_history.html', context)

@login_required
@patient_required
def patient_billing(request):
    """View billing information"""
    patient = get_object_or_404(Patient, user=request.user)
    bills = Billing.objects.filter(patient=patient).order_by('-created_at')
    
    paginator = Paginator(bills, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'bills': page_obj,
        'patient': patient,
        'total_unpaid': bills.filter(is_paid=False).count(),
    }
    return render(request, 'patients/billing.html', context)

@login_required
@patient_required
def patient_prescriptions(request):
    """View patient prescriptions"""
    patient = get_object_or_404(Patient, user=request.user)
    prescriptions = Prescription.objects.filter(patient=patient).order_by('-created_at') if Prescription else []
    
    paginator = Paginator(prescriptions, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'patients/prescriptions.html', {'prescriptions': page_obj})

@login_required
@patient_required
def edit_patient_profile(request):
    """Edit patient profile"""
    patient = get_object_or_404(Patient, user=request.user)
    
    if request.method == 'POST':
        # Update patient information
        patient.emergency_contact = request.POST.get('emergency_contact', patient.emergency_contact)
        patient.blood_group = request.POST.get('blood_group', patient.blood_group)
        patient.allergies = request.POST.get('allergies', patient.allergies)
        patient.medical_history = request.POST.get('medical_history', patient.medical_history)
        patient.save()
        
        # Update user information
        user = patient.user
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        user.phone = request.POST.get('phone', user.phone)
        user.address = request.POST.get('address', user.address)
        user.save()
        
        messages.success(request, 'Profile updated successfully!')
        return redirect('patients:profile')
    
    return render(request, 'patients/edit_profile.html', {'patient': patient})

# Placeholder views for features under construction
@login_required
@patient_required
def cancel_appointment(request, appointment_id):
    """Cancel appointment"""
    if Appointment:
        try:
            appointment = get_object_or_404(Appointment, id=appointment_id, patient__user=request.user)
            appointment.status = 'cancelled'
            appointment.save()
            messages.success(request, 'Appointment cancelled successfully!')
        except:
            messages.error(request, 'Error cancelling appointment.')
    else:
        messages.info(request, 'Cancel appointment feature coming soon!')
    return redirect('patients:appointments')

@login_required
@patient_required
def reschedule_appointment(request, appointment_id):
    """Reschedule appointment"""
    messages.info(request, 'Reschedule appointment feature coming soon!')
    return redirect('patients:appointments')

@login_required
@patient_required
def medical_record_detail(request, record_id):
    """View medical record detail"""
    patient = get_object_or_404(Patient, user=request.user)
    try:
        record = get_object_or_404(MedicalRecord, id=record_id, patient=patient)
        return render(request, 'patients/medical_record_detail.html', {'record': record, 'patient': patient})
    except:
        messages.error(request, 'Medical record not found.')
        return redirect('patients:medical_history')

@login_required
@patient_required
def bill_detail(request, bill_id):
    """View bill detail"""
    patient = get_object_or_404(Patient, user=request.user)
    try:
        bill = get_object_or_404(Billing, id=bill_id, patient=patient)
        return render(request, 'patients/bill_detail.html', {'bill': bill, 'patient': patient})
    except:
        messages.error(request, 'Bill not found.')
        return redirect('patients:billing')

@login_required
@patient_required
def pay_bill(request, bill_id):
    """Pay bill"""
    patient = get_object_or_404(Patient, user=request.user)
    try:
        bill = get_object_or_404(Billing, id=bill_id, patient=patient)
        
        if request.method == 'POST':
            # Simulate payment processing
            bill.is_paid = True
            bill.paid_at = timezone.now()
            bill.save()
            messages.success(request, f'Bill of ${bill.amount} paid successfully!')
            return redirect('patients:billing')
        
        return render(request, 'patients/pay_bill.html', {'bill': bill, 'patient': patient})
    except:
        messages.error(request, 'Bill not found.')
        return redirect('patients:billing')

@login_required
@patient_required
def health_resources(request):
    """View health resources"""
    resources = [
        {
            'id': 1, 
            'title': 'Healthy Living Guide', 
            'description': 'Tips for maintaining a healthy lifestyle',
            'category': 'General Health'
        },
        {
            'id': 2, 
            'title': 'Managing Diabetes', 
            'description': 'Important information on managing diabetes',
            'category': 'Chronic Conditions'
        },
        {
            'id': 3, 
            'title': 'Heart Health', 
            'description': 'Keeping your heart healthy',
            'category': 'Cardiovascular'
        },
        {
            'id': 4, 
            'title': 'Mental Wellness', 
            'description': 'Mental health and wellness tips',
            'category': 'Mental Health'
        },
    ]
    return render(request, 'patients/health_resources.html', {'resources': resources})

@login_required
@patient_required
def health_resource_detail(request, resource_id):
    """View health resource detail"""
    # This would typically fetch from database
    sample_resources = {
        1: {
            'title': 'Healthy Living Guide',
            'content': 'Detailed content about healthy living...',
            'category': 'General Health'
        },
        2: {
            'title': 'Managing Diabetes',
            'content': 'Detailed content about diabetes management...',
            'category': 'Chronic Conditions'
        }
    }
    
    resource = sample_resources.get(int(resource_id))
    if not resource:
        messages.error(request, 'Resource not found.')
        return redirect('patients:health_resources')
    
    return render(request, 'patients/health_resource_detail.html', {'resource': resource})

@login_required
@patient_required
def prescription_detail(request, prescription_id):
    """View prescription detail"""
    patient = get_object_or_404(Patient, user=request.user)
    
    if Prescription:
        try:
            prescription = get_object_or_404(Prescription, id=prescription_id, patient=patient)
            return render(request, 'patients/prescription_detail.html', {
                'prescription': prescription, 
                'patient': patient
            })
        except:
            messages.error(request, 'Prescription not found.')
    else:
        messages.info(request, 'Prescription detail feature coming soon!')
    
    return redirect('patients:prescriptions')

@login_required
@patient_required
def appointment_detail(request, appointment_id):
    """View appointment detail"""
    patient = get_object_or_404(Patient, user=request.user)
    
    if Appointment:
        try:
            appointment = get_object_or_404(Appointment, id=appointment_id, patient=patient)
            return render(request, 'patients/appointment_detail.html', {
                'appointment': appointment, 
                'patient': patient
            })
        except:
            messages.error(request, 'Appointment not found.')
    else:
        messages.info(request, 'Appointment detail feature coming soon!')
    
    return redirect('patients:appointments')
