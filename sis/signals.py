from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import StaffProfile, SubjectAssessment, Notification, StaffClassSubject


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


@receiver(post_save, sender=SubjectAssessment)
def notify_form_teacher_on_assessment_update(sender, instance, created, **kwargs):
    student = instance.student
    enrollments = student.enrollments.all()
    if not enrollments.exists():
        return

    target_classroom = enrollments.order_by('-date_enrolled').first().classroom
    form_teacher_staff = StaffClassSubject.objects.filter(
        classroom=target_classroom, subject=instance.subject
    ).select_related('staff', 'staff__user').first()

    if form_teacher_staff and form_teacher_staff.staff.user:
        Notification.objects.create(
            recipient=form_teacher_staff.staff.user,
            title="Assessment Scores Updated",
            message=(
                f"Scores for {instance.subject.subject_name} have been "
                f"{'added' if created else 'updated'} for {target_classroom.class_name}."
            ),
            notification_type='ASSESSMENT_UPDATE',
        )
