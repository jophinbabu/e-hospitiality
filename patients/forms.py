from django import forms
from django.core.exceptions import ValidationError
from core.models import Appointment
from doctors.models import Doctor
from datetime import datetime, timedelta
import pytz

class AppointmentForm(forms.ModelForm):
    doctor = forms.ModelChoiceField(
        queryset=Doctor.objects.all(),
        empty_label="Select a Doctor",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    appointment_date = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={
            'type': 'datetime-local',
            'class': 'form-control'
        }),
        help_text="Select date and time for your appointment"
    )
    
    reason = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Describe your medical concern...'
        }),
        max_length=500
    )
    
    class Meta:
        model = Appointment
        fields = ['doctor', 'appointment_date', 'reason']
    
    def clean_appointment_date(self):
        appointment_date = self.cleaned_data.get('appointment_date')
        
        # Check if appointment is in the future
        if appointment_date and appointment_date <= datetime.now(pytz.timezone('Asia/Kolkata')):
            raise ValidationError('Appointment must be scheduled for a future date and time.')
        
        return appointment_date
    
    def clean(self):
        cleaned_data = super().clean()
        doctor = cleaned_data.get('doctor')
        appointment_date = cleaned_data.get('appointment_date')
        
        if doctor and appointment_date:
            # Check if doctor already has appointment at this time
            existing_appointment = Appointment.objects.filter(
                doctor=doctor,
                appointment_date=appointment_date
            ).exists()
            
            if existing_appointment:
                raise ValidationError(
                    f'Dr. {doctor.user.get_full_name()} already has an appointment scheduled at {appointment_date.strftime("%B %d, %Y at %I:%M %p")}. '
                    'Please choose a different time slot.'
                )
        
        return cleaned_data
