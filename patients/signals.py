from django.db.models.signals import post_save
from django.dispatch import receiver
from core.models import CustomUser
from .models import Patient

@receiver(post_save, sender=CustomUser)
def create_patient_profile(sender, instance, created, **kwargs):
    """Automatically create Patient profile when user_type is patient"""
    if created and instance.user_type == 'patient':
        Patient.objects.create(
            user=instance,
            patient_id=f"P{instance.id:06d}"
        )

@receiver(post_save, sender=CustomUser)
def save_patient_profile(sender, instance, **kwargs):
    """Save patient profile when user is saved"""
    if instance.user_type == 'patient' and hasattr(instance, 'patient'):
        instance.patient.save()
