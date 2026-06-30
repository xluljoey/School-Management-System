from django.contrib import admin
from .models import ClassRoom, Subject, StaffProfile, Student, SubjectAssignment, AcademicSession, Term, ClassSubject, Parent, Department, Designation, StaffClassSubject


class StaffClassSubjectInline(admin.TabularInline):
    model = StaffClassSubject
    extra = 3
    verbose_name = "Assigned Class & Subject"
    verbose_name_plural = "Assigned Classes & Subjects"


@admin.register(StaffProfile)
class StaffProfileAdmin(admin.ModelAdmin):
    inlines = [StaffClassSubjectInline]


class ClassSubjectAdmin(admin.ModelAdmin):
    list_display = ('classroom', 'subject')
    list_filter = ('classroom', 'subject')
    search_fields = ('classroom__class_name', 'subject__subject_name')

admin.site.register(ClassRoom)
admin.site.register(Subject)
admin.site.register(Student)
admin.site.register(SubjectAssignment)
admin.site.register(AcademicSession)
admin.site.register(Term)
admin.site.register(ClassSubject, ClassSubjectAdmin)
admin.site.register(Parent)
admin.site.register(Department)
admin.site.register(Designation)
admin.site.register(StaffClassSubject)
