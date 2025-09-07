from django.db.models.signals import post_save
from django.dispatch import receiver
from core.models import CustomUser
from .models import Doctor

@receiver(post_save, sender=CustomUser)
def create_doctor_profile(sender, instance, created, **kwargs):
    """Automatically create Doctor profile when user_type is doctor"""
    if created and instance.user_type == 'doctor':
        Doctor.objects.create(
            user=instance,
            doctor_id=f"DR{instance.id:06d}",
            specialization="General Medicine",
            license_number=f"MD{instance.id:06d}",
            experience_years=1,
            consultation_fee=100.00
        )

@receiver(post_save, sender=CustomUser)
def save_doctor_profile(sender, instance, **kwargs):
    """Save doctor profile when user is saved"""
    if instance.user_type == 'doctor' and hasattr(instance, 'doctor'):
        instance.doctor.save()
