from django.urls import path
from .views import student_list_view, student_registration_view, bulk_grade_entry_view, class_report_card_view

urlpatterns = [
    path('students/', student_list_view, name='student_list'),
    path('students/register/', student_registration_view, name='student_registration'),
    path('students/report/<int:class_id>/', class_report_card_view, name='class_report_card'),
    path('class/<int:class_id>/report/', class_report_card_view, name='class_report_card_short'),
    path('class/<int:class_id>/report/view/', class_report_card_view, name='class_report'),
    path('students/grades/', bulk_grade_entry_view, name='bulk_grade_entry'),
    #Dynamic parameter layout captures which class and subject grid user is updating
    path('grades/entry/<int:class_id>/<int:subject_id>/', bulk_grade_entry_view, name='bulk_grade_entry'),
]
