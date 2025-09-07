from django.db import models
from django.utils import timezone
from core.models import CustomUser, Department

class Doctor(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    doctor_id = models.CharField(max_length=20, unique=True, blank=True)
    specialization = models.CharField(max_length=100, default="General Medicine")
    license_number = models.CharField(max_length=50, blank=True)
    experience_years = models.PositiveIntegerField(default=1)
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2, default=100.00)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    def save(self, *args, **kwargs):
        if not self.doctor_id:
            self.doctor_id = f"DR{self.user.id:06d}"
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Dr. {self.user.first_name} {self.user.last_name}"

class Prescription(models.Model):
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE)
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    medications = models.TextField()
    dosage = models.TextField()
    instructions = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Prescription for {self.patient}"
