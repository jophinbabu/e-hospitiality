from django.db import models
from django.utils import timezone
from django.conf import settings  # ✅ Use settings instead of direct import

class Patient(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  # ✅ Fixed
    patient_id = models.CharField(max_length=20, unique=True, blank=True)
    blood_group = models.CharField(max_length=5, blank=True, null=True)
    allergies = models.TextField(blank=True, null=True)
    emergency_contact = models.CharField(max_length=15, blank=True, null=True)
    medical_history = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)

    def save(self, *args, **kwargs):
        if not self.patient_id:
            self.patient_id = f"P{self.user.id:06d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name} (ID: {self.patient_id})"

class MedicalRecord(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    doctor = models.ForeignKey('doctors.Doctor', on_delete=models.CASCADE)
    diagnosis = models.TextField()
    symptoms = models.TextField(blank=True)
    treatment_notes = models.TextField(blank=True)
    medications = models.TextField(blank=True)
    date_created = models.DateTimeField(default=timezone.now)
    follow_up_date = models.DateField(blank=True, null=True)

    class Meta:
        ordering = ['-date_created']

class Billing(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    description = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    paid_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        status = "Paid" if self.is_paid else "Unpaid"
        return f"Bill - {self.patient} - ₹{self.amount} ({status})"
