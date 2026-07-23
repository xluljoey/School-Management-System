from .models import StaffProfile, AcademicSession, Term, Notification


def staff_context(request):
    if request.user.is_authenticated:
        staff_profile = getattr(request.user, 'staff_profile', None)
        subject_count = staff_profile.assigned_classes_subjects.values('subject').distinct().count() if staff_profile else 0

        current_session = AcademicSession.objects.filter(is_current=True).first()
        current_term = Term.objects.filter(is_active=True).first() if current_session else None
        is_promotional_term = current_term and current_term.term_name == 'Term 3'

        unread_notifications = Notification.objects.filter(
            recipient=request.user, is_read=False
        )
        unread_count = unread_notifications.count()
        recent_notifications = Notification.objects.filter(
            recipient=request.user
        )[:20]

        return {
            'staff_profile': staff_profile,
            'subject_count': subject_count,
            'active_session': current_session,
            'active_term': current_term,
            'is_promotional_term': is_promotional_term,
            'unread_notification_count': unread_count,
            'recent_notifications': recent_notifications,
        }
    return {}
