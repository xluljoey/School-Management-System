from django.contrib import admin
from .models import ClassRoom, Subject, StaffProfile, Student, SubjectAssignment, AcademicSession, Term, ClassSubject, Parent

# Register your models here.
class ClassSubjectAdmin(admin.ModelAdmin):
    list_display = ('classroom', 'subject')
    list_filter = ('classroom', 'subject')
    search_fields = ('classroom__class_name', 'subject__subject_name')

admin.site.register(ClassRoom)
admin.site.register(Subject)
admin.site.register(StaffProfile)
admin.site.register(Student)
admin.site.register(SubjectAssignment)
admin.site.register(AcademicSession)
admin.site.register(Term)
admin.site.register(ClassSubject, ClassSubjectAdmin)
admin.site.register(Parent)
