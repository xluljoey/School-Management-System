from django.contrib import admin
from .models import ClassRoom, Subject, StaffProfile, Student, SubjectAssignment

# Register your models here.
admin.site.register(ClassRoom)
admin.site.register(Subject)
admin.site.register(StaffProfile)
admin.site.register(Student)
admin.site.register(SubjectAssignment)
