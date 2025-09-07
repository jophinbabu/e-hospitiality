from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from core.models import CustomUser, Department, Appointment
from patients.models import Patient, Billing, MedicalRecord
from doctors.models import Doctor, Prescription
from .forms import UserCreationForm, DepartmentForm, BillingForm

def admin_required(view_func):
    """Decorator to ensure only admins can access the view"""
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.user_type != 'admin':
            messages.error(request, 'Access denied. Admins only.')
            return redirect('core:home')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

@login_required
@admin_required
def admin_dashboard(request):
    """Admin dashboard view"""
    # Get statistics
    total_users = CustomUser.objects.count()
    total_patients = Patient.objects.count()
    total_doctors = Doctor.objects.count()
    total_appointments = Appointment.objects.count()
    total_departments = Department.objects.count()
    
    context = {
        'total_users': total_users,
        'total_patients': total_patients,
        'total_doctors': total_doctors,
        'total_appointments': total_appointments,
        'total_departments': total_departments,
    }
    return render(request, 'admins/dashboard.html', context)

@login_required
@admin_required
def user_management(request):
    """User management view"""
    users = CustomUser.objects.all().order_by('-date_joined')
    
    paginator = Paginator(users, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'users': page_obj,
    }
    return render(request, 'admins/user_management.html', context)

@login_required
@admin_required
def appointment_management(request):
    """Appointment management view"""
    appointments = Appointment.objects.all().order_by('-appointment_date')
    
    paginator = Paginator(appointments, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'appointments': page_obj,
    }
    return render(request, 'admins/appointment_management.html', context)

# Placeholder views for other admin functions
@login_required
@admin_required
def billing_management(request):
    """Billing management view"""
    messages.info(request, 'Billing management feature coming soon!')
    return redirect('admins:dashboard')

@login_required
@admin_required
def reports(request):
    """Reports view"""
    messages.info(request, 'Reports feature coming soon!')
    return redirect('admins:dashboard')

@login_required
@admin_required
def system_settings(request):
    """System settings view"""
    messages.info(request, 'System settings feature coming soon!')
    return redirect('admins:dashboard')
