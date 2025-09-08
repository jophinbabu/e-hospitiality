import razorpay
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.conf import settings
from django.contrib import messages
from .models import Payment
from doctors.models import Doctor
from core.models import Appointment
import uuid

# Initialize Razorpay Client
razorpay_client = razorpay.Client(
    auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
)

@login_required
def initiate_payment(request, appointment_id=None, doctor_id=None):
    """Initiate payment for consultation or appointment"""
    
    if appointment_id:
        appointment = get_object_or_404(Appointment, id=appointment_id, patient__user=request.user)
        amount = float(appointment.doctor.consultation_fee)
        description = f"Consultation fee for Dr. {appointment.doctor.user.get_full_name()}"
        payment_type = 'consultation'
        doctor = appointment.doctor
    elif doctor_id:
        doctor = get_object_or_404(Doctor, id=doctor_id)
        amount = float(doctor.consultation_fee)
        description = f"Consultation fee for Dr. {doctor.user.get_full_name()}"
        payment_type = 'consultation'
        appointment = None
    else:
        messages.error(request, 'Invalid payment request.')
        return redirect('core:home')
    
    # Convert to paise (Razorpay works in smallest currency unit)
    amount_in_paise = int(amount * 100)
    
    # Generate unique payment ID
    payment_id = str(uuid.uuid4())
    
    # Create Razorpay Order
    try:
        razorpay_order = razorpay_client.order.create({
            'amount': amount_in_paise,
            'currency': 'INR',
            'payment_capture': '0'  # Manual capture
        })
    except Exception as e:
        messages.error(request, f'Payment initialization failed: {str(e)}')
        return redirect('core:home')
    
    # Create Payment record
    payment = Payment.objects.create(
        user=request.user,
        doctor=doctor,
        appointment=appointment,
        payment_id=payment_id,
        razorpay_order_id=razorpay_order['id'],
        amount=amount,
        payment_type=payment_type,
        description=description
    )
    
    context = {
        'payment': payment,
        'razorpay_order_id': razorpay_order['id'],
        'razorpay_key_id': settings.RAZORPAY_KEY_ID,
        'amount': amount_in_paise,
        'currency': 'INR',
        'doctor': doctor,
        'appointment': appointment,
    }
    
    return render(request, 'payments/checkout.html', context)

@csrf_exempt
def payment_success(request):
    """Handle successful payment callback"""
    if request.method == 'POST':
        try:
            # Get payment details from POST data
            razorpay_payment_id = request.POST.get('razorpay_payment_id')
            razorpay_order_id = request.POST.get('razorpay_order_id')
            razorpay_signature = request.POST.get('razorpay_signature')
            
            # Verify payment signature
            params_dict = {
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_signature': razorpay_signature
            }
            
            result = razorpay_client.utility.verify_payment_signature(params_dict)
            
            if result:
                # Update payment record
                payment = get_object_or_404(Payment, razorpay_order_id=razorpay_order_id)
                payment.razorpay_payment_id = razorpay_payment_id
                payment.razorpay_signature = razorpay_signature
                payment.status = 'completed'
                payment.save()
                
                # Capture payment
                try:
                    razorpay_client.payment.capture(
                        razorpay_payment_id, 
                        int(payment.amount * 100)
                    )
                except Exception as e:
                    # Payment verification successful but capture failed
                    messages.warning(request, 'Payment verified but capture failed. Please contact support.')
                
                # Update appointment status if applicable
                if payment.appointment:
                    payment.appointment.status = 'confirmed'
                    payment.appointment.save()
                
                messages.success(request, 'Payment completed successfully!')
                return render(request, 'payments/success.html', {'payment': payment})
            else:
                messages.error(request, 'Payment verification failed.')
                return render(request, 'payments/failed.html')
                
        except Exception as e:
            messages.error(request, f'Payment processing failed: {str(e)}')
            return render(request, 'payments/failed.html', {'error': str(e)})
    
    return redirect('core:home')

@login_required
def payment_failed(request):
    """Handle payment failure"""
    error_message = request.GET.get('error', 'Payment was not completed successfully')
    context = {
        'error': error_message
    }
    return render(request, 'payments/failed.html', context)

@login_required
def payment_history(request):
    """View payment history"""
    payments = Payment.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'payments': payments
    }
    
    return render(request, 'payments/history.html', context)
