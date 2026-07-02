from .models import StaffProfile


def staff_context(request):
    if request.user.is_authenticated:
        staff_profile = getattr(request.user, 'staff_profile', None)
        subject_count = staff_profile.assigned_classes_subjects.values('subject').distinct().count() if staff_profile else 0
        return {
            'staff_profile': staff_profile,
            'subject_count': subject_count,
        }
    return {}
