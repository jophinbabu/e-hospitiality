from django import forms
from .models import Patient

class PatientProfileForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = ['emergency_contact', 'blood_group', 'allergies']
        widgets = {
            'emergency_contact': forms.TextInput(attrs={'class': 'form-control'}),
            'blood_group': forms.TextInput(attrs={'class': 'form-control'}),
            'allergies': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class AppointmentForm(forms.Form):
    doctor = forms.ChoiceField(widget=forms.Select(attrs={'class': 'form-control'}))
    appointment_date = forms.DateTimeField(widget=forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}))
    reason = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}))
