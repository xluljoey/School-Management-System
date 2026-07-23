from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import StaffProfile


@receiver(post_save, sender=StaffProfile)
def create_staff_user_account(sender, instance, created, **kwargs):
    if created and not instance.user:
        user_account = User.objects.create_user(
            username=instance.staff_id,
            email=instance.email,
            password="staff123",
        )
        instance.user = user_account
        instance.save()
