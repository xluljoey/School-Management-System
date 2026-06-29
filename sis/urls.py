from django.urls import path
from django.views.generic.base import RedirectView
from .views import (
    student_list_view,
    student_registration_view,
    enroll_student_view,
    bulk_grade_entry_view,
    class_report_card_view,
    register_staff_view,
    login_view,
    logout_view,
    class_enrollment_portal_view,
    configure_session_view,
)

urlpatterns = [
    path('', RedirectView.as_view(url='/students/', permanent=False), name='home'),
    path('e', RedirectView.as_view(url='/students/', permanent=False), name='e_redirect'),
    path('students/', student_list_view, name='student_list'),
    path('students/register/', student_registration_view, name='student_registration'),
    path('students/enroll/<int:student_id>/', enroll_student_view, name='enroll_student'),
    path('students/report/<int:class_id>/', class_report_card_view, name='class_report_card'),
    path('class/<int:class_id>/report/', class_report_card_view, name='class_report_card_short'),
    path('class/<int:class_id>/report/view/', class_report_card_view, name='class_report'),
    path('staff/register/', register_staff_view, name='register_staff'),
    # Primary bulk grade-entry route: requires both class_id and subject_id.
    path('grades/entry/<int:class_id>/<int:subject_id>/', bulk_grade_entry_view, name='bulk_grade_entry'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('enrollment/portal/', class_enrollment_portal_view, name='class_enrollment_portal'),
    path('settings/academic-session/', configure_session_view, name='configure_session'),
]
