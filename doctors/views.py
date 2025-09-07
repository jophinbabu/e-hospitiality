from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.http import JsonResponse, HttpResponse
from django.template.defaultfilters import timesince
from django.urls import reverse
from datetime import datetime, timedelta
import json

from .models import Doctor, Prescription

# Import models conditionally to avoid circular imports
try:
    from patients.models import Patient, MedicalRecord
    from core.models import Appointment, Department
except ImportError:
    Patient = None
    MedicalRecord = None
    Appointment = None
    Department = None


def doctor_required(view_func):
    """Decorator to ensure only doctors can access the view"""
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.user_type != 'doctor':
            messages.error(request, 'Access denied. Doctors only.')
            return redirect('core:home')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


@login_required
@doctor_required
def doctor_dashboard(request):
    """Doctor dashboard view with comprehensive statistics"""
    try:
        doctor = Doctor.objects.get(user=request.user)
    except Doctor.DoesNotExist:
        # Create doctor profile if it doesn't exist
        doctor = Doctor.objects.create(
            user=request.user,
            doctor_id=f"DR{request.user.id:06d}",
            specialization="General Medicine",
            license_number=f"MD{request.user.id:06d}",
            experience_years=1,
            consultation_fee=100.00
        )
        messages.success(request, 'Doctor profile created successfully!')
    
    # Get doctor's statistics
    context = {'doctor': doctor}
    
    if Appointment:
        today = timezone.now().date()
        tomorrow = today + timedelta(days=1)
        this_week = today + timedelta(days=7)
        this_month = today + timedelta(days=30)
        
        # Today's appointments
        today_appointments = Appointment.objects.filter(
            doctor=doctor,
            appointment_date__date=today
        ).order_by('appointment_date')
        
        # Tomorrow's appointments
        tomorrow_appointments = Appointment.objects.filter(
            doctor=doctor,
            appointment_date__date=tomorrow
        ).order_by('appointment_date')
        
        # Weekly and monthly stats
        total_appointments_today = today_appointments.count()
        total_appointments_week = Appointment.objects.filter(
            doctor=doctor,
            appointment_date__date__range=[today, this_week]
        ).count()
        total_appointments_month = Appointment.objects.filter(
            doctor=doctor,
            appointment_date__date__range=[today, this_month]
        ).count()
        
        # Status-based counts
        pending_appointments = Appointment.objects.filter(
            doctor=doctor,
            status='scheduled'
        ).count()
        
        completed_appointments = Appointment.objects.filter(
            doctor=doctor,
            status='completed'
        ).count()
        
        cancelled_appointments = Appointment.objects.filter(
            doctor=doctor,
            status='cancelled'
        ).count()
        
        # Upcoming appointments
        upcoming_appointments = Appointment.objects.filter(
            doctor=doctor,
            appointment_date__gte=timezone.now(),
            status='scheduled'
        ).order_by('appointment_date')[:10]
        
        # Recent appointments
        recent_appointments = Appointment.objects.filter(
            doctor=doctor
        ).order_by('-appointment_date')[:5]
        
        context.update({
            'total_appointments_today': total_appointments_today,
            'total_appointments_week': total_appointments_week,
            'total_appointments_month': total_appointments_month,
            'pending_appointments': pending_appointments,
            'completed_appointments': completed_appointments,
            'cancelled_appointments': cancelled_appointments,
            'today_appointments': today_appointments,
            'tomorrow_appointments': tomorrow_appointments,
            'upcoming_appointments': upcoming_appointments,
            'recent_appointments': recent_appointments,
        })
    else:
        context.update({
            'total_appointments_today': 0,
            'total_appointments_week': 0,
            'total_appointments_month': 0,
            'pending_appointments': 0,
            'completed_appointments': 0,
            'cancelled_appointments': 0,
            'today_appointments': [],
            'tomorrow_appointments': [],
            'upcoming_appointments': [],
            'recent_appointments': [],
        })
    
    if Patient and Appointment:
        # Patient statistics
        total_patients = Patient.objects.filter(
            appointment__doctor=doctor
        ).distinct().count()
        
        new_patients_this_month = Patient.objects.filter(
            appointment__doctor=doctor,
            appointment__appointment_date__gte=today.replace(day=1)
        ).distinct().count()
        
        recent_patients = Patient.objects.filter(
            appointment__doctor=doctor
        ).distinct().order_by('-appointment__appointment_date')[:5]
        
        context.update({
            'total_patients': total_patients,
            'new_patients_this_month': new_patients_this_month,
            'recent_patients': recent_patients,
        })
    else:
        context.update({
            'total_patients': 0,
            'new_patients_this_month': 0,
            'recent_patients': [],
        })
    
    # Prescription statistics
    total_prescriptions = Prescription.objects.filter(doctor=doctor).count()
    recent_prescriptions = Prescription.objects.filter(
        doctor=doctor
    ).order_by('-created_at')[:5]
    
    prescriptions_this_month = Prescription.objects.filter(
        doctor=doctor,
        created_at__gte=today.replace(day=1)
    ).count()
    
    context.update({
        'total_prescriptions': total_prescriptions,
        'prescriptions_this_month': prescriptions_this_month,
        'recent_prescriptions': recent_prescriptions,
    })
    
    return render(request, 'doctors/dashboard.html', context)


@login_required
@doctor_required
def doctor_appointments(request):
    """View doctor's appointments with advanced filtering"""
    doctor = get_object_or_404(Doctor, user=request.user)
    
    if not Appointment:
        context = {'doctor': doctor, 'appointments': []}
        return render(request, 'doctors/appointments.html', context)
    
    # Get all appointments for this doctor
    appointments_list = Appointment.objects.filter(doctor=doctor)
    
    # Apply filters
    status_filter = request.GET.get('status')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    search_query = request.GET.get('search')
    
    if status_filter:
        appointments_list = appointments_list.filter(status=status_filter)
    
    if date_from:
        try:
            date_from_parsed = datetime.strptime(date_from, '%Y-%m-%d').date()
            appointments_list = appointments_list.filter(appointment_date__date__gte=date_from_parsed)
        except ValueError:
            messages.warning(request, 'Invalid date format for "From Date".')
    
    if date_to:
        try:
            date_to_parsed = datetime.strptime(date_to, '%Y-%m-%d').date()
            appointments_list = appointments_list.filter(appointment_date__date__lte=date_to_parsed)
        except ValueError:
            messages.warning(request, 'Invalid date format for "To Date".')
    
    if search_query:
        appointments_list = appointments_list.filter(
            Q(patient__user__first_name__icontains=search_query) |
            Q(patient__user__last_name__icontains=search_query) |
            Q(patient__user__email__icontains=search_query) |
            Q(reason__icontains=search_query) |
            Q(notes__icontains=search_query)
        )
    
    appointments_list = appointments_list.order_by('-appointment_date')
    
    # Pagination
    paginator = Paginator(appointments_list, 15)
    page_number = request.GET.get('page')
    appointments = paginator.get_page(page_number)
    
    # Statistics for cards
    today = timezone.now().date()
    today_appointments = appointments_list.filter(appointment_date__date=today)
    pending_appointments = appointments_list.filter(status='scheduled').count()
    completed_appointments = appointments_list.filter(status='completed').count()
    cancelled_appointments = appointments_list.filter(status='cancelled').count()
    
    context = {
        'doctor': doctor,
        'appointments': appointments,
        'today_appointments': today_appointments,
        'pending_appointments': pending_appointments,
        'completed_appointments': completed_appointments,
        'cancelled_appointments': cancelled_appointments,
        'today': today,
        'search_query': search_query,
        'status_filter': status_filter,
        'date_from': date_from,
        'date_to': date_to,
    }
    
    return render(request, 'doctors/appointments.html', context)


@login_required
@doctor_required
def create_appointment(request):
    """Create new appointment view for doctors"""
    doctor = get_object_or_404(Doctor, user=request.user)
    
    if not Patient or not Appointment:
        messages.error(request, 'Appointment system not available.')
        return redirect('doctors:dashboard')
    
    if request.method == 'POST':
        try:
            patient_id = request.POST.get('patient')
            appointment_date = request.POST.get('appointment_date')
            appointment_time = request.POST.get('appointment_time')
            reason = request.POST.get('reason')
            notes = request.POST.get('notes', '')
            
            # Validation
            if not all([patient_id, appointment_date, appointment_time, reason]):
                messages.error(request, 'Please fill in all required fields.')
                return redirect('doctors:create_appointment')
            
            # Get patient
            try:
                patient = Patient.objects.get(id=patient_id)
            except Patient.DoesNotExist:
                messages.error(request, 'Selected patient does not exist.')
                return redirect('doctors:create_appointment')
            
            # Combine date and time
            appointment_datetime = timezone.datetime.strptime(
                f"{appointment_date} {appointment_time}",
                "%Y-%m-%d %H:%M"
            )
            appointment_datetime = timezone.make_aware(appointment_datetime)
            
            # Check if appointment time is in the future
            if appointment_datetime <= timezone.now():
                messages.error(request, 'Appointment date and time must be in the future.')
                return redirect('doctors:create_appointment')
            
            # Check for conflicting appointments
            conflicting_appointments = Appointment.objects.filter(
                doctor=doctor,
                appointment_date=appointment_datetime,
                status='scheduled'
            )
            
            if conflicting_appointments.exists():
                messages.error(request, 'You already have an appointment scheduled at this time.')
                return redirect('doctors:create_appointment')
            
            # Create appointment
            appointment = Appointment.objects.create(
                patient=patient,
                doctor=doctor,
                appointment_date=appointment_datetime,
                reason=reason,
                notes=notes,
                status='scheduled'
            )
            
            messages.success(request, f'Appointment scheduled successfully for {patient.user.get_full_name()} on {appointment_datetime.strftime("%B %d, %Y at %I:%M %p")}!')
            return redirect('doctors:appointments')
            
        except ValueError as e:
            messages.error(request, 'Invalid date or time format.')
            return redirect('doctors:create_appointment')
        except Exception as e:
            messages.error(request, f'Error creating appointment: {str(e)}')
            return redirect('doctors:create_appointment')
    
    # Get patients for dropdown
    patients = Patient.objects.all().order_by('user__first_name', 'user__last_name')
    
    # Generate time slots (9 AM to 5 PM, 30-minute intervals)
    time_slots = []
    for hour in range(9, 17):
        for minute in [0, 30]:
            time_obj = timezone.time(hour, minute)
            time_slots.append(time_obj.strftime('%H:%M'))
    
    context = {
        'doctor': doctor,
        'patients': patients,
        'today': timezone.now().date(),
        'time_slots': time_slots,
    }
    
    return render(request, 'doctors/create_appointment.html', context)


@login_required
@doctor_required
def doctor_patients(request):
    """View doctor's patients with search functionality"""
    doctor = get_object_or_404(Doctor, user=request.user)
    
    if not Patient or not Appointment:
        context = {'doctor': doctor, 'patients': []}
        return render(request, 'doctors/patients.html', context)
    
    # Get patients who have appointments with this doctor
    patients_list = Patient.objects.filter(
        appointment__doctor=doctor
    ).distinct()
    
    # Apply search filter
    search_query = request.GET.get('search')
    if search_query:
        patients_list = patients_list.filter(
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(user__email__icontains=search_query) |
            Q(patient_id__icontains=search_query)
        )
    
    patients_list = patients_list.order_by('user__first_name', 'user__last_name')
    
    # Annotate with additional data
    for patient in patients_list:
        # Get last appointment date
        last_appointment = Appointment.objects.filter(
            patient=patient, doctor=doctor
        ).order_by('-appointment_date').first()
        
        patient.last_appointment_date = last_appointment.appointment_date if last_appointment else None
        
        # Count total appointments
        patient.total_appointments = Appointment.objects.filter(
            patient=patient, doctor=doctor
        ).count()
        
        # Get age if date of birth is available
        if hasattr(patient.user, 'date_of_birth') and patient.user.date_of_birth:
            age_timesince = timesince(patient.user.date_of_birth)
            patient.age = age_timesince.split(',')[0] if ',' in age_timesince else age_timesince
        else:
            patient.age = None
    
    # Pagination
    paginator = Paginator(patients_list, 12)
    page_number = request.GET.get('page')
    patients = paginator.get_page(page_number)
    
    # Statistics for cards
    active_appointments = Appointment.objects.filter(
        doctor=doctor, status='scheduled'
    ).count()
    
    total_prescriptions = Prescription.objects.filter(doctor=doctor).count()
    
    context = {
        'doctor': doctor,
        'patients': patients,
        'search_query': search_query,
        'active_appointments': active_appointments,
        'total_prescriptions': total_prescriptions,
    }
    
    return render(request, 'doctors/patients.html', context)


@login_required
@doctor_required
def doctor_prescriptions(request):
    """View doctor's prescriptions with search and filter"""
    doctor = get_object_or_404(Doctor, user=request.user)
    
    prescriptions_list = Prescription.objects.filter(
        doctor=doctor
    ).select_related('patient__user')
    
    # Apply search filter
    search_query = request.GET.get('search')
    if search_query:
        prescriptions_list = prescriptions_list.filter(
            Q(patient__user__first_name__icontains=search_query) |
            Q(patient__user__last_name__icontains=search_query) |
            Q(medications__icontains=search_query) |
            Q(diagnosis__icontains=search_query)
        )
    
    # Date filter
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    if date_from:
        try:
            date_from_parsed = datetime.strptime(date_from, '%Y-%m-%d').date()
            prescriptions_list = prescriptions_list.filter(created_at__date__gte=date_from_parsed)
        except ValueError:
            messages.warning(request, 'Invalid date format for "From Date".')
    
    if date_to:
        try:
            date_to_parsed = datetime.strptime(date_to, '%Y-%m-%d').date()
            prescriptions_list = prescriptions_list.filter(created_at__date__lte=date_to_parsed)
        except ValueError:
            messages.warning(request, 'Invalid date format for "To Date".')
    
    prescriptions_list = prescriptions_list.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(prescriptions_list, 12)
    page_number = request.GET.get('page')
    prescriptions = paginator.get_page(page_number)
    
    context = {
        'doctor': doctor,
        'prescriptions': prescriptions,
        'search_query': search_query,
        'date_from': date_from,
        'date_to': date_to,
    }
    
    return render(request, 'doctors/prescriptions.html', context)


@login_required
@doctor_required
def doctor_schedule(request):
    """View doctor's schedule with weekly view"""
    doctor = get_object_or_404(Doctor, user=request.user)
    
    # Get current week or requested week
    date_str = request.GET.get('date')
    if date_str:
        try:
            base_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            base_date = timezone.now().date()
    else:
        base_date = timezone.now().date()
    
    # Calculate week boundaries
    start_date = base_date - timedelta(days=base_date.weekday())
    end_date = start_date + timedelta(days=6)
    
    # Previous and next week dates
    prev_week = start_date - timedelta(days=7)
    next_week = start_date + timedelta(days=7)
    
    # Generate week dates for each day (Monday to Sunday)
    week_dates = []
    day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    for i in range(7):
        day_date = start_date + timedelta(days=i)
        week_dates.append({
            'date': day_date,
            'name': day_names[i],
            'is_today': day_date == timezone.now().date()
        })
    
    if Appointment:
        appointments = Appointment.objects.filter(
            doctor=doctor,
            appointment_date__date__range=[start_date, end_date]
        ).order_by('appointment_date')
        
        # Organize appointments by day and hour for easier template rendering
        schedule_grid = {}
        for i in range(7):  # Days of week (0=Monday, 6=Sunday)
            day_date = start_date + timedelta(days=i)
            schedule_grid[i] = {}
            for hour in range(9, 18):  # Hours 9 AM to 5 PM
                day_appointments = appointments.filter(
                    appointment_date__date=day_date,
                    appointment_date__hour=hour
                )
                schedule_grid[i][hour] = list(day_appointments)
    else:
        appointments = []
        schedule_grid = {}
    
    # Get weekly statistics
    total_appointments = appointments.count() if appointments else 0
    completed_appointments = appointments.filter(status='completed').count() if appointments else 0
    pending_appointments = appointments.filter(status='scheduled').count() if appointments else 0
    
    # Time slots for the schedule (9 AM to 5 PM)
    time_slots = []
    for hour in range(9, 18):
        time_slots.append({
            'hour': hour,
            'display': f"{hour:02d}:00",
            'display_12h': f"{hour if hour <= 12 else hour-12}:00 {'AM' if hour < 12 else 'PM'}"
        })
    
    context = {
        'doctor': doctor,
        'appointments': appointments,
        'schedule_grid': schedule_grid,
        'start_date': start_date,
        'end_date': end_date,
        'prev_week': prev_week,
        'next_week': next_week,
        'today': timezone.now().date(),
        'total_appointments': total_appointments,
        'completed_appointments': completed_appointments,
        'pending_appointments': pending_appointments,
        'week_dates': week_dates,
        'time_slots': time_slots,
    }
    
    return render(request, 'doctors/schedule.html', context)

    """View doctor's schedule with weekly view"""
    doctor = get_object_or_404(Doctor, user=request.user)
    
    # Get current week or requested week
    date_str = request.GET.get('date')
    if date_str:
        try:
            base_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            base_date = timezone.now().date()
    else:
        base_date = timezone.now().date()
    
    # Calculate week boundaries
    start_date = base_date - timedelta(days=base_date.weekday())
    end_date = start_date + timedelta(days=6)
    
    # Previous and next week dates
    prev_week = start_date - timedelta(days=7)
    next_week = start_date + timedelta(days=7)
    
    if Appointment:
        appointments = Appointment.objects.filter(
            doctor=doctor,
            appointment_date__date__range=[start_date, end_date]
        ).order_by('appointment_date')
        
        # Organize appointments by day
        schedule = {}
        for i in range(7):
            day_date = start_date + timedelta(days=i)
            schedule[day_date] = appointments.filter(appointment_date__date=day_date)
    else:
        appointments = []
        schedule = {}
    
    # Get weekly statistics
    total_appointments = appointments.count() if appointments else 0
    completed_appointments = appointments.filter(status='completed').count() if appointments else 0
    pending_appointments = appointments.filter(status='scheduled').count() if appointments else 0
    
    context = {
        'doctor': doctor,
        'appointments': appointments,
        'schedule': schedule,
        'start_date': start_date,
        'end_date': end_date,
        'prev_week': prev_week,
        'next_week': next_week,
        'today': timezone.now().date(),
        'total_appointments': total_appointments,
        'completed_appointments': completed_appointments,
        'pending_appointments': pending_appointments,
    }
    
    return render(request, 'doctors/schedule.html', context)


@login_required
@doctor_required
def create_prescription(request, patient_id=None):
    """Create new prescription with enhanced form"""
    doctor = get_object_or_404(Doctor, user=request.user)
    
    if not Patient:
        messages.error(request, 'Patient system not available.')
        return redirect('doctors:prescriptions')
    
    if patient_id:
        patient = get_object_or_404(Patient, id=patient_id)
    else:
        patient = None
    
    if request.method == 'POST':
        try:
            if not patient:
                patient_id = request.POST.get('patient_id')
                if not patient_id:
                    messages.error(request, 'Please select a patient.')
                    return redirect(request.path)
                patient = get_object_or_404(Patient, id=patient_id)
            
            medications = request.POST.get('medications', '').strip()
            dosage = request.POST.get('dosage', '').strip()
            instructions = request.POST.get('instructions', '').strip()
            diagnosis = request.POST.get('diagnosis', '').strip()
            
            # Validation
            if not all([medications, dosage, instructions]):
                messages.error(request, 'Please fill in all required fields (medications, dosage, and instructions).')
                return redirect(request.path)
            
            # Create prescription
            prescription = Prescription.objects.create(
                patient=patient,
                doctor=doctor,
                medications=medications,
                dosage=dosage,
                instructions=instructions,
                diagnosis=diagnosis
            )
            
            messages.success(request, f'Prescription created successfully for {patient.user.get_full_name()}!')
            return redirect('doctors:prescription_detail', prescription_id=prescription.id)
            
        except Exception as e:
            messages.error(request, f'Error creating prescription: {str(e)}')
    
    # Get patients for dropdown
    patients = Patient.objects.all().order_by('user__first_name', 'user__last_name')
    
    # Get patient's medical history if patient is selected
    patient_history = []
    if patient:
        patient_history = Prescription.objects.filter(
            patient=patient, doctor=doctor
        ).order_by('-created_at')[:5]
    
    context = {
        'doctor': doctor,
        'patient': patient,
        'patients': patients,
        'patient_history': patient_history,
    }
    
    return render(request, 'doctors/create_prescription.html', context)


@login_required
@doctor_required
def appointment_detail(request, appointment_id):
    """View detailed appointment information"""
    doctor = get_object_or_404(Doctor, user=request.user)
    
    if not Appointment:
        messages.error(request, 'Appointment system not available.')
        return redirect('doctors:appointments')
    
    appointment = get_object_or_404(Appointment, id=appointment_id, doctor=doctor)
    
    # Get patient's appointment history with this doctor
    patient_appointments = Appointment.objects.filter(
        patient=appointment.patient, doctor=doctor
    ).exclude(id=appointment_id).order_by('-appointment_date')[:5]
    
    # Get patient's prescriptions from this doctor
    patient_prescriptions = Prescription.objects.filter(
        patient=appointment.patient, doctor=doctor
    ).order_by('-created_at')[:3]
    
    context = {
        'appointment': appointment,
        'doctor': doctor,
        'patient_appointments': patient_appointments,
        'patient_prescriptions': patient_prescriptions,
    }
    
    return render(request, 'doctors/appointment_detail.html', context)


@login_required
@doctor_required
def complete_appointment(request, appointment_id):
    """Mark appointment as completed with optional notes"""
    doctor = get_object_or_404(Doctor, user=request.user)
    
    if not Appointment:
        messages.error(request, 'Appointment system not available.')
        return redirect('doctors:appointments')
    
    appointment = get_object_or_404(Appointment, id=appointment_id, doctor=doctor)
    
    if request.method == 'POST':
        completion_notes = request.POST.get('completion_notes', '')
        
        if appointment.status == 'scheduled':
            appointment.status = 'completed'
            if completion_notes:
                appointment.notes = appointment.notes + f"\n\nCompletion Notes: {completion_notes}" if appointment.notes else f"Completion Notes: {completion_notes}"
            appointment.save()
            
            messages.success(request, f'Appointment with {appointment.patient.user.get_full_name()} marked as completed!')
        else:
            messages.warning(request, 'This appointment cannot be marked as completed.')
        
        return redirect('doctors:appointments')
    
    # If GET request, show confirmation form
    context = {
        'appointment': appointment,
        'doctor': doctor,
    }
    return render(request, 'doctors/complete_appointment.html', context)


@login_required
@doctor_required
def cancel_appointment(request, appointment_id):
    """Cancel appointment with reason"""
    doctor = get_object_or_404(Doctor, user=request.user)
    
    if not Appointment:
        messages.error(request, 'Appointment system not available.')
        return redirect('doctors:appointments')
    
    appointment = get_object_or_404(Appointment, id=appointment_id, doctor=doctor)
    
    if request.method == 'POST':
        cancellation_reason = request.POST.get('cancellation_reason', '')
        
        if appointment.status == 'scheduled':
            appointment.status = 'cancelled'
            if cancellation_reason:
                appointment.notes = appointment.notes + f"\n\nCancellation Reason: {cancellation_reason}" if appointment.notes else f"Cancellation Reason: {cancellation_reason}"
            appointment.save()
            
            messages.success(request, f'Appointment with {appointment.patient.user.get_full_name()} has been cancelled!')
        else:
            messages.warning(request, 'This appointment cannot be cancelled.')
        
        return redirect('doctors:appointments')
    
    # If GET request, show confirmation form
    context = {
        'appointment': appointment,
        'doctor': doctor,
    }
    return render(request, 'doctors/cancel_appointment.html', context)


@login_required
@doctor_required
def patient_detail(request, patient_id):
    """Comprehensive patient detail view"""
    doctor = get_object_or_404(Doctor, user=request.user)
    
    if not Patient:
        messages.error(request, 'Patient system not available.')
        return redirect('doctors:patients')
    
    patient = get_object_or_404(Patient, id=patient_id)
    
    # Get patient's appointments with this doctor
    appointments = []
    medical_records = []
    
    if Appointment:
        appointments = Appointment.objects.filter(
            patient=patient, doctor=doctor
        ).order_by('-appointment_date')
        
        # Get appointment statistics
        total_appointments = appointments.count()
        completed_appointments = appointments.filter(status='completed').count()
        scheduled_appointments = appointments.filter(status='scheduled').count()
        cancelled_appointments = appointments.filter(status='cancelled').count()
    else:
        total_appointments = 0
        completed_appointments = 0
        scheduled_appointments = 0
        cancelled_appointments = 0
    
    if MedicalRecord:
        medical_records = MedicalRecord.objects.filter(
            patient=patient, doctor=doctor
        ).order_by('-date_created')
    
    # Get patient's prescriptions from this doctor
    prescriptions = Prescription.objects.filter(
        patient=patient, doctor=doctor
    ).order_by('-created_at')
    
    # Calculate patient age if date of birth is available
    patient_age = None
    if hasattr(patient.user, 'date_of_birth') and patient.user.date_of_birth:
        age_timesince = timesince(patient.user.date_of_birth)
        patient_age = age_timesince.split(',')[0] if ',' in age_timesince else age_timesince
    
    context = {
        'doctor': doctor,
        'patient': patient,
        'patient_age': patient_age,
        'appointments': appointments,
        'medical_records': medical_records,
        'prescriptions': prescriptions,
        'total_appointments': total_appointments,
        'completed_appointments': completed_appointments,
        'scheduled_appointments': scheduled_appointments,
        'cancelled_appointments': cancelled_appointments,
    }
    
    return render(request, 'doctors/patient_detail.html', context)


@login_required
@doctor_required
def doctor_profile(request):
    """Enhanced doctor profile view and edit"""
    doctor = get_object_or_404(Doctor, user=request.user)
    
    if request.method == 'POST':
        try:
            # Update doctor information
            doctor.specialization = request.POST.get('specialization', doctor.specialization).strip()
            doctor.license_number = request.POST.get('license_number', doctor.license_number).strip()
            
            # Validate and update experience years
            try:
                doctor.experience_years = int(request.POST.get('experience_years', doctor.experience_years))
            except (ValueError, TypeError):
                doctor.experience_years = 1
            
            # Validate and update consultation fee
            try:
                doctor.consultation_fee = float(request.POST.get('consultation_fee', doctor.consultation_fee))
            except (ValueError, TypeError):
                doctor.consultation_fee = 100.00
            
            doctor.is_available = 'is_available' in request.POST
            doctor.bio = request.POST.get('bio', getattr(doctor, 'bio', '')).strip()
            
            doctor.save()
            
            # Update user information
            user = doctor.user
            user.first_name = request.POST.get('first_name', user.first_name).strip()
            user.last_name = request.POST.get('last_name', user.last_name).strip()
            user.email = request.POST.get('email', user.email).strip()
            
            # Update phone if the field exists
            phone = request.POST.get('phone', '').strip()
            if hasattr(user, 'phone'):
                user.phone = phone
            
            user.save()
            
            messages.success(request, 'Profile updated successfully!')
            return redirect('doctors:profile')
            
        except Exception as e:
            messages.error(request, f'Error updating profile: {str(e)}')
    
    # Get profile statistics
    total_appointments = 0
    total_patients = 0
    total_prescriptions = Prescription.objects.filter(doctor=doctor).count()
    
    if Appointment:
        total_appointments = Appointment.objects.filter(doctor=doctor).count()
        
    if Patient and Appointment:
        total_patients = Patient.objects.filter(
            appointment__doctor=doctor
        ).distinct().count()
    
    context = {
        'doctor': doctor,
        'total_appointments': total_appointments,
        'total_patients': total_patients,
        'total_prescriptions': total_prescriptions,
    }
    
    return render(request, 'doctors/profile.html', context)


@login_required
@doctor_required
def prescription_detail(request, prescription_id):
    """Detailed prescription view with patient context"""
    doctor = get_object_or_404(Doctor, user=request.user)
    prescription = get_object_or_404(Prescription, id=prescription_id, doctor=doctor)
    
    # Get patient's other prescriptions from this doctor
    other_prescriptions = Prescription.objects.filter(
        patient=prescription.patient, doctor=doctor
    ).exclude(id=prescription_id).order_by('-created_at')[:5]
    
    # Get patient's appointment history
    patient_appointments = []
    if Appointment:
        patient_appointments = Appointment.objects.filter(
            patient=prescription.patient, doctor=doctor
        ).order_by('-appointment_date')[:5]
    
    context = {
        'prescription': prescription,
        'doctor': doctor,
        'other_prescriptions': other_prescriptions,
        'patient_appointments': patient_appointments,
    }
    
    return render(request, 'doctors/prescription_detail.html', context)


# API Views for AJAX requests
@login_required
@doctor_required
def get_patient_info(request, patient_id):
    """AJAX endpoint to get patient information"""
    if not Patient:
        return JsonResponse({'error': 'Patient system not available'}, status=400)
    
    try:
        patient = Patient.objects.get(id=patient_id)
        
        # Get patient's appointment history with this doctor
        doctor = get_object_or_404(Doctor, user=request.user)
        recent_appointments = []
        
        if Appointment:
            appointments = Appointment.objects.filter(
                patient=patient, doctor=doctor
            ).order_by('-appointment_date')[:3]
            
            for apt in appointments:
                recent_appointments.append({
                    'date': apt.appointment_date.strftime('%Y-%m-%d %H:%M'),
                    'status': apt.status,
                    'reason': apt.reason
                })
        
        data = {
            'name': patient.user.get_full_name(),
            'email': patient.user.email,
            'phone': getattr(patient, 'phone', ''),
            'patient_id': getattr(patient, 'patient_id', ''),
            'recent_appointments': recent_appointments
        }
        
        return JsonResponse(data)
        
    except Patient.DoesNotExist:
        return JsonResponse({'error': 'Patient not found'}, status=404)


# Placeholder views for features under construction
@login_required
@doctor_required
def set_availability(request):
    """Set doctor availability - placeholder"""
    messages.info(request, 'Set availability feature coming soon!')
    return redirect('doctors:schedule')


@login_required
@doctor_required
def medical_records(request):
    """Medical records management - placeholder"""
    messages.info(request, 'Medical records feature coming soon!')
    return redirect('doctors:dashboard')


@login_required
@doctor_required
def export_data(request):
    """Export doctor's data - placeholder"""
    messages.info(request, 'Data export feature coming soon!')
    return redirect('doctors:dashboard')


@login_required
@doctor_required
def doctor_analytics(request):
    """Doctor analytics dashboard - placeholder"""
    messages.info(request, 'Analytics dashboard coming soon!')
    return redirect('doctors:dashboard')
