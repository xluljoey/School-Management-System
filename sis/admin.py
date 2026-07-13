from django.contrib import admin
from .models import ClassRoom, Subject, StaffProfile, Student, SubjectAssignment, AcademicSession, Term, ClassSubject, Parent, Department, Designation, StaffClassSubject, MidTermRecord

class PermissiveModelAdmin(admin.ModelAdmin):
    """
    A ModelAdmin class that grants view/change permissions to all staff users.
    Useful for development and testing environments.
    """
    def has_view_or_change_permission(self, request, obj=None):
        # Grant permission if user is staff (for development/testing)
        return request.user.is_staff or super().has_view_or_change_permission(request, obj)
    
    def has_module_permission(self, request):
        # Grant module permission if user is staff (for development/testing)
        return request.user.is_staff or super().has_module_permission(request)


class StaffClassSubjectInline(admin.TabularInline):
    model = StaffClassSubject
    extra = 3
    verbose_name = "Assigned Class & Subject"
    verbose_name_plural = "Assigned Classes & Subjects"


@admin.register(StaffProfile)
class StaffProfileAdmin(PermissiveModelAdmin):
    inlines = [StaffClassSubjectInline]


class ClassSubjectAdmin(PermissiveModelAdmin):
    list_display = ('classroom', 'subject')
    list_filter = ('classroom', 'subject')
    search_fields = ('classroom__class_name', 'subject__subject_name')
    actions = ['clone_class_subjects']

    @admin.action(description="Clone selected subjects to another class")
    def clone_class_subjects(self, request, queryset):
        from django.shortcuts import render
        from django.http import HttpResponseRedirect
        from .models import ClassRoom

        if 'apply' in request.POST:
            target_class_id = request.POST.get('target_classroom')
            target_classroom = ClassRoom.objects.get(id=target_class_id)

            cloned_count = 0
            for class_subject in queryset:
                obj, created = ClassSubject.objects.get_or_create(
                    classroom=target_classroom,
                    subject=class_subject.subject
                )
                if created:
                    cloned_count += 1

            self.message_user(request, f"Successfully cloned {cloned_count} subjects to {target_classroom.class_name}.")
            return HttpResponseRedirect(request.get_full_path())

        classrooms = ClassRoom.objects.exclude(
            id__in=queryset.values_list('classroom_id', flat=True).distinct()
        )

        return render(request, 'admin/clone_subjects_intermediate.html', context={
            'selected_subjects': queryset,
            'classrooms': classrooms,
            'action_checkbox_name': admin.helpers.ACTION_CHECKBOX_NAME,
        })


@admin.register(Student)
class StudentAdmin(PermissiveModelAdmin):
    list_display = ('admission_number', 'first_name', 'last_name', 'gender', 'classroom')
    list_editable = ('classroom',)
    list_filter = ('classroom', 'gender', 'status')
    search_fields = ('admission_number', 'first_name', 'last_name')

admin.site.register(ClassRoom, type('ClassRoomAdmin', (PermissiveModelAdmin,), {
    'list_display': ('class_name', 'order', 'form_teacher'),
    'search_fields': ('class_name',),
}))
admin.site.register(Subject, PermissiveModelAdmin)
admin.site.register(SubjectAssignment, PermissiveModelAdmin)
admin.site.register(AcademicSession, PermissiveModelAdmin)
admin.site.register(Term, PermissiveModelAdmin)
admin.site.register(ClassSubject, ClassSubjectAdmin)
admin.site.register(Parent, PermissiveModelAdmin)
admin.site.register(Department, PermissiveModelAdmin)
admin.site.register(Designation, PermissiveModelAdmin)
admin.site.register(StaffClassSubject, PermissiveModelAdmin)
admin.site.register(MidTermRecord, PermissiveModelAdmin)
