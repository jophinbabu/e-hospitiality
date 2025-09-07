from django import forms
from .models import Doctor, Prescription
from patients.models import MedicalRecord

class DoctorProfileForm(forms.ModelForm):
    class Meta:
        model = Doctor
        fields = ['specialization', 'experience_years', 'consultation_fee']
        widgets = {
            'specialization': forms.TextInput(attrs={'class': 'form-control'}),
            'experience_years': forms.NumberInput(attrs={'class': 'form-control'}),
            'consultation_fee': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class PrescriptionForm(forms.ModelForm):
    class Meta:
        model = Prescription
        fields = ['medications', 'dosage', 'instructions']
        widgets = {
            'medications': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'dosage': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'instructions': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class MedicalRecordForm(forms.ModelForm):
    class Meta:
        model = MedicalRecord
        fields = ['diagnosis', 'medications', 'treatment_notes']
        widgets = {
            'diagnosis': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'medications': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'treatment_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }
