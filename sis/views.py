from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.db.models import Q, Count
from django.http import JsonResponse
from django.urls import reverse
from django.views.decorators.http import require_POST
import json
from .models import (
    Parent, Student, Subject, SubjectAssessment, ClassRoom, Enrollment,
    StaffProfile, AcademicSession, Term, ClassSubject, PromotionCriteria,
    StaffClassSubject, Department, Designation, GradeVerification,
    MidTermRecord,
)
from .forms import (
    ParentForm, StudentRegistrationForm, StaffRegistrationForm, EnrollmentForm,
    MarkSubmissionForm,
)

# Create your views here.
@login_required
def dashboard_view(request):
    is_admin = request.user.is_superuser or request.user.groups.filter(name='Admin').exists()

    if is_admin:
        context = {
            'total_staff_count': StaffProfile.objects.count(),
            'environment': 'Academic Year Master Control',
        }
        return render(request, 'sis/admin_dashboard.html', context)

    total_students = Student.objects.count()
    total_staff = StaffProfile.objects.count()
    active_classes = ClassRoom.objects.count()
    current_session = AcademicSession.objects.filter(is_current=True).first()
    current_term = Term.objects.filter(is_active=True).first() if current_session else None

    total_boys = Student.objects.filter(gender__iexact='Male').count()
    total_girls = Student.objects.filter(gender__iexact='Female').count()
    boy_pct = int((total_boys / total_students) * 100) if total_students > 0 else 0
    girl_pct = int((total_girls / total_students) * 100) if total_students > 0 else 0

    staff_profile = getattr(request.user, 'staff_profile', None)

    if request.user.is_superuser:
        assigned_classes = ClassRoom.objects.all()
    elif staff_profile:
        assigned_class_ids = StaffClassSubject.objects.filter(staff=staff_profile).values_list('classroom_id', flat=True).distinct()
        assigned_classes = ClassRoom.objects.filter(id__in=assigned_class_ids) if assigned_class_ids else ClassRoom.objects.none()
    else:
        assigned_classes = ClassRoom.objects.none()

    staff_student_count = 0
    staff_subject_count = 0
    active_environment_string = ''

    if staff_profile and not request.user.is_superuser:
        if assigned_class_ids:
            staff_student_count = Student.objects.filter(enrollments__classroom_id__in=assigned_class_ids).distinct().count()
        staff_subject_count = Subject.objects.filter(assigned_teachers__staff=staff_profile).distinct().count()

    if current_term:
        term_name = current_term.term_name
    elif current_session:
        term_name = 'Term 1'
    else:
        term_name = ''
    active_environment_string = f"{term_name}, {current_session.academic_year}" if current_session and term_name else (str(current_session) if current_session else '')

    context = {
        'total_students': total_students,
        'total_staff': total_staff,
        'active_classes': active_classes,
        'current_session': current_session,
        'current_term': current_term,
        'total_boys': total_boys,
        'total_girls': total_girls,
        'boy_pct': boy_pct,
        'girl_pct': girl_pct,
        'staff_student_count': staff_student_count,
        'staff_subject_count': staff_subject_count,
        'active_environment_string': active_environment_string,
        'assigned_classes': assigned_classes,
    }
    return render(request, 'sis/staff_dashboard.html', context)


@login_required
def student_list_view(request):
    students = Student.objects.all().select_related('classroom')
    classrooms = ClassRoom.objects.all()
    return render(request, 'sis/student_list.html', {
        'students': students,
        'classrooms': classrooms,
    })


@login_required
def student_detail_view(request, student_id):
    student = get_object_or_404(Student, pk=student_id)
    return render(request, 'sis/student_detail.html', {'student': student})


@login_required
def student_edit_view(request, student_id):
    student = get_object_or_404(Student, pk=student_id)
    if request.method == 'POST':
        student_form = StudentRegistrationForm(request.POST, request.FILES, instance=student)
        if student_form.is_valid():
            student_form.save()
            messages.success(request, 'Student updated successfully.')
            return redirect('student_detail', student_id=student.id)
    else:
        student_form = StudentRegistrationForm(instance=student)
    return render(request, 'sis/student_registration.html', {
        'student_form': student_form,
        'is_edit': True,
        'edit_student': student,
    })


@login_required
def student_registration_view(request):
    if request.method == 'POST':
        student_form = StudentRegistrationForm(request.POST, request.FILES)
        father_form = ParentForm(request.POST, prefix='father')
        mother_form = ParentForm(request.POST, prefix='mother')

        if student_form.is_valid() and father_form.is_valid() and mother_form.is_valid():
            student_instance = student_form.save(commit=False)
            
            # Save parent forms if they have data
            father_obj = None
            mother_obj = None
            
            # Check if father form has any data
            father_has_data = any([
                father_form.cleaned_data.get('name'),
                father_form.cleaned_data.get('telephone_number')
            ])
            
            if father_has_data:
                father_obj = father_form.save()
            
            # Check if mother form has any data
            mother_has_data = any([
                mother_form.cleaned_data.get('name'),
                mother_form.cleaned_data.get('telephone_number')
            ])
            
            if mother_has_data:
                mother_obj = mother_form.save()
            
            # Link them directly to the student row
            student_instance.father = father_obj
            student_instance.mother = mother_obj
            student_instance.save()
            return redirect('enroll_student', student_id=student_instance.id)
    else:
        student_form = StudentRegistrationForm()
        father_form = ParentForm(prefix='father')
        mother_form = ParentForm(prefix='mother')

    return render(request, 'sis/student_registration.html', {
        'student_form': student_form,
        'father_form': father_form,
        'mother_form': mother_form,
    })

def _is_staff_or_admin(user):
    return user.is_active and (user.is_superuser or user.is_staff or hasattr(user, 'staff_profile'))


def _is_admin(user):
    return user.is_active and user.is_superuser


# bulk score processing view
@login_required
def bulk_grade_entry_view(request, class_id, subject_id):
    if not _is_staff_or_admin(request.user):
        raise PermissionDenied
    classroom = ClassRoom.objects.get(pk=class_id)
    staff = getattr(request.user, 'staff_profile', None)

    if not request.user.is_superuser:
        has_assignment = StaffClassSubject.objects.filter(staff=staff, classroom=classroom, subject_id=subject_id).exists()
        if not has_assignment:
            messages.error(request, 'You can only enter grades for subjects and classes assigned to you.')
            return redirect('dashboard')

    students = Student.objects.filter(enrollments__classroom=classroom).distinct()
    if request.user.is_superuser:
        subjects = Subject.objects.all().order_by('subject_name')
    else:
        assigned_subject_ids = StaffClassSubject.objects.filter(staff=staff, classroom=classroom).values_list('subject_id', flat=True).distinct()
        subjects = Subject.objects.filter(id__in=assigned_subject_ids).order_by('subject_name')

    if subject_id:
        subject = Subject.objects.filter(pk=subject_id).first()
    else:
        subject = subjects.first()

    if subject is None:
        return render(request, 'sis/bulk_grade_entry.html', {
            'classroom': classroom,
            'subjects': subjects,
            'subject': None,
            'matrix': [],
            'message': 'No subjects are available yet.'
        })

    # static anchors for current tracking context
    current_session = AcademicSession.objects.filter(is_current=True).first()
    current_term_obj = Term.objects.filter(is_active=True).first()
    current_term = int(current_term_obj.term_name.split()[-1]) if current_term_obj else 1
    current_academic_year = current_session.academic_year if current_session else "2025-2026"

    if request.method == 'POST':
        for student in students:
            # safety grab input values from the raw POST stream using unique field id
            class_val = request.POST.get(f'class_score_{student.id}')
            exam_val = request.POST.get(f'exam_score_{student.id}')
            
            if class_val and exam_val:
                SubjectAssessment.objects.update_or_create(
                    student=student,
                    subject=subject,
                    academic_session=current_session,
                    academic_term=current_term_obj,
                    defaults={
                        'class_score': class_val,
                        'exam_score': exam_val,
                        'term': current_term,
                        'academic_year': current_academic_year,
                    }
                )
        messages.success(request, f"Grades for {subject.subject_name} saved successfully!")
        return redirect('bulk_grade_entry', class_id=class_id, subject_id=subject_id)
    
    # Build up existing data list to repopulate inputs if scores are already entered
    student_marks_matrix = []
    for student in students:
        existing_assessment = SubjectAssessment.objects.filter(
                student=student, subject=subject, academic_session=current_session, academic_term=current_term_obj
            ).first()
        
        student_marks_matrix.append({
            'student': student,
            'existing_class_score': existing_assessment.class_score if existing_assessment else "",
            'existing_exam_score': existing_assessment.exam_score if existing_assessment else ""
        })

    context = {
        'classroom': classroom,
        'subject': subject,
        'subjects': subjects,
        'matrix': student_marks_matrix
    }
    return render(request, 'sis/bulk_grade_entry.html', context)

@login_required
def class_report_card_view(request, class_id):
    if not _is_staff_or_admin(request.user):
        raise PermissionDenied
    classroom = ClassRoom.objects.get(pk=class_id)

    staff = getattr(request.user, 'staff_profile', None)
    is_form_teacher = staff and staff.form_class == classroom
    has_full_access = request.user.is_superuser or is_form_teacher

    try:
        user_form_class = request.user.staff_profile.form_class
    except AttributeError:
        user_form_class = None

    current_subject_id = request.GET.get('subject_id')
    if current_subject_id and not current_subject_id.isdigit():
        current_subject_id = None

    if request.user.is_superuser:
        assigned_subjects = Subject.objects.filter(offered_in_classes__classroom=classroom).distinct()
    elif staff:
        assigned_ids = StaffClassSubject.objects.filter(staff=staff, classroom=classroom).values_list('subject_id', flat=True).distinct()
        assigned_subjects = Subject.objects.filter(id__in=assigned_ids) if assigned_ids else Subject.objects.none()
    else:
        assigned_subjects = Subject.objects.none()

    students = Student.objects.filter(enrollments__classroom=classroom).distinct()

    current_session = AcademicSession.objects.filter(is_current=True).first()
    current_term = Term.objects.filter(is_active=True).first()

    report_data = []
    for student in students:
        assessments = SubjectAssessment.objects.filter(student=student, academic_session=current_session, academic_term=current_term)
        if not has_full_access and staff:
            assigned_subject_ids = StaffClassSubject.objects.filter(staff=staff, classroom=classroom).values_list('subject_id', flat=True).distinct()
            assessments = assessments.filter(subject_id__in=assigned_subject_ids)
        if current_subject_id:
            assessments = assessments.filter(subject_id=current_subject_id)
        grand_total = sum(ast.total_score for ast in assessments)
        first = assessments.first()
        report_data.append({
            'student': student,
            'assessments': assessments,
            'grand_total': grand_total,
            'class_score': f"{first.class_score:.1f}" if first else None,
            'exam_score': f"{first.exam_score:.1f}" if first else None,
        })

    report_data = sorted(report_data, key=lambda x: x['grand_total'], reverse=True)

    for index, row in enumerate(report_data):
        row['rank'] = index + 1

    if request.user.is_superuser:
        classrooms = ClassRoom.objects.all()
    else:
        assigned_ids = StaffClassSubject.objects.filter(staff=staff).values_list('classroom_id', flat=True).distinct()
        classrooms = ClassRoom.objects.filter(id__in=assigned_ids) if assigned_ids else ClassRoom.objects.none()
    has_graded_records = any(row['assessments'].exists() for row in report_data)

    # Determine if the current user can modify grades for this class/subject
    can_modify_grades = has_full_access
    if not can_modify_grades and staff:
        if current_subject_id and current_subject_id.isdigit():
            can_modify_grades = StaffClassSubject.objects.filter(
                staff=staff,
                classroom=classroom,
                subject_id=current_subject_id
            ).exists()
        else:
            can_modify_grades = assigned_subjects.exists()

    current_term = Term.objects.filter(is_active=True).first()
    term_number = int(current_term.term_name.split()[-1]) if current_term else 1
    year_label = current_term.session.academic_year if current_term and current_term.session else "2025/2026"

    verification = GradeVerification.objects.filter(
        classroom=classroom, term=term_number, academic_year=year_label
    ).first()

    return render(request, 'sis/class_report.html', {
        'classroom': classroom,
        'report_data': report_data,
        'classrooms': classrooms,
        'assigned_classes': classrooms,
        'current_class_id': classroom.id,
        'user_form_class': user_form_class,
        'has_graded_records': has_graded_records,
        'is_form_teacher': is_form_teacher,
        'has_full_access': has_full_access,
        'verification': verification,
        'assigned_subjects': assigned_subjects,
        'current_subject_id': int(current_subject_id) if current_subject_id and current_subject_id.isdigit() else None,
        'can_modify_grades': can_modify_grades,
    })


@login_required
def register_staff_view(request):
    departments = Department.objects.all()
    designations = Designation.objects.all()
    all_classrooms = ClassRoom.objects.all()

    if request.method == 'POST':
        form = StaffRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            # Create the staff profile first
            staff_profile = form.save(commit=False)

            # Handle department FK
            dept_name = form.cleaned_data.get('department')
            if dept_name:
                dept, _ = Department.objects.get_or_create(name=dept_name)
                staff_profile.department = dept

            # Handle designation FK
            desig_name = form.cleaned_data.get('designation')
            if desig_name:
                desig, _ = Designation.objects.get_or_create(name=desig_name)
                staff_profile.designation = desig

            # Parse full_name into first/last/other if the individual fields weren't
            # populated directly by the form (the form still carries `full_name`).
            full = getattr(staff_profile, 'full_name', '') or ''
            if full and not staff_profile.first_name:
                parts = full.strip().split(None, 2)
                staff_profile.first_name = parts[0] if len(parts) > 0 else ''
                staff_profile.last_name = parts[-1] if len(parts) > 1 else ''
                staff_profile.other_names = ' '.join(parts[1:-1]) if len(parts) > 2 else ''

            # Create a corresponding user account using staff_id as username
            username = staff_profile.staff_id
            password = 'staff123'  # Default password

            # Create user if it doesn't exist
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'first_name': staff_profile.first_name,
                    'last_name': staff_profile.last_name,
                    'email': staff_profile.email,
                    'is_staff': True,
                }
            )

            # Set the password if user was just created
            if created:
                user.set_password(password)
                user.save()

            # Link the user to the staff profile
            staff_profile.user = user
            staff_profile.save()
            form.save_m2m()

            # Parse assignments_json and bulk-create StaffClassSubject records
            assignments_raw = request.POST.get('assignments_json', '')
            if assignments_raw:
                try:
                    import json
                    assignments = json.loads(assignments_raw)
                    for class_id_str, subject_ids in assignments.items():
                        for subj_id in subject_ids:
                            StaffClassSubject.objects.get_or_create(
                                staff=staff_profile,
                                classroom_id=int(class_id_str),
                                subject_id=int(subj_id)
                            )
                except (json.JSONDecodeError, ValueError):
                    pass

            messages.success(request, f'Staff member registered successfully. Username: {username}, Password: {password}')
            return redirect('staff_list')
    else:
        form = StaffRegistrationForm()

    return render(request, 'sis/register_staff.html', {
        'form': form,
        'departments': departments,
        'designations': designations,
        'all_classrooms': all_classrooms,
    })


@login_required
def staff_list_view(request):
    staff_members = StaffProfile.objects.select_related('user').all()
    return render(request, 'sis/staff_list.html', {'staff_members': staff_members})


@login_required
def staff_detail_view(request, staff_id):
    staff_member = get_object_or_404(StaffProfile, pk=staff_id)
    all_classes = ClassRoom.objects.all()
    assignments = StaffClassSubject.objects.filter(
        staff=staff_member
    ).select_related('classroom', 'subject')
    return render(request, 'sis/staff_detail.html', {
        'staff_member': staff_member,
        'all_classes': all_classes,
        'assignments': assignments,
    })


@login_required
@require_POST
def assign_form_class(request, staff_id):
    if not (request.user.is_superuser or request.user.is_staff):
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)

    data = json.loads(request.body)
    class_id = data.get('class_id')

    target_staff = get_object_or_404(StaffProfile, pk=staff_id)
    target_class = get_object_or_404(ClassRoom, pk=class_id)

    try:
        old_teacher = target_class.form_teacher
        if old_teacher:
            old_teacher.form_class = None
            old_teacher.save()
    except StaffProfile.DoesNotExist:
        pass

    target_staff.form_class = target_class
    target_staff.save()

    return JsonResponse({'success': True})


@login_required
def staff_edit_view(request, staff_id):
    import json
    staff_member = get_object_or_404(StaffProfile, pk=staff_id)
    departments = Department.objects.all()
    designations = Designation.objects.all()
    all_classrooms = ClassRoom.objects.all()

    # Build existing assignments for the JS picker
    existing_assignments = {}
    for scs in staff_member.assigned_classes_subjects.select_related('classroom', 'subject').all():
        class_id = str(scs.classroom_id)
        if class_id not in existing_assignments:
            existing_assignments[class_id] = []
        existing_assignments[class_id].append(str(scs.subject_id))

    if request.method == 'POST':
        form = StaffRegistrationForm(request.POST, request.FILES, instance=staff_member)
        if form.is_valid():
            staff_profile = form.save(commit=False)

            dept_name = form.cleaned_data.get('department')
            if dept_name:
                dept, _ = Department.objects.get_or_create(name=dept_name)
                staff_profile.department = dept
            else:
                staff_profile.department = None

            desig_name = form.cleaned_data.get('designation')
            if desig_name:
                desig, _ = Designation.objects.get_or_create(name=desig_name)
                staff_profile.designation = desig
            else:
                staff_profile.designation = None

            user = staff_profile.user
            if user:
                user.first_name = staff_profile.first_name
                user.last_name = staff_profile.last_name
                user.email = staff_profile.email
                user.save()

            staff_profile.save()
            form.save_m2m()

            # Replace all ClassSubject assignments
            staff_profile.assigned_classes_subjects.all().delete()
            assignments_raw = request.POST.get('assignments_json', '')
            if assignments_raw:
                try:
                    assignments = json.loads(assignments_raw)
                    for class_id_str, subject_ids in assignments.items():
                        for subj_id in subject_ids:
                            StaffClassSubject.objects.get_or_create(
                                staff=staff_profile,
                                classroom_id=int(class_id_str),
                                subject_id=int(subj_id)
                            )
                except (json.JSONDecodeError, ValueError):
                    pass

            messages.success(request, 'Staff member updated successfully.')
            return redirect('staff_detail', staff_id=staff_profile.id)
    else:
        form = StaffRegistrationForm(instance=staff_member)
        if staff_member.department:
            form.fields['department'].initial = staff_member.department.name
        if staff_member.designation:
            form.fields['designation'].initial = staff_member.designation.name

    return render(request, 'sis/register_staff.html', {
        'form': form,
        'departments': departments,
        'designations': designations,
        'all_classrooms': all_classrooms,
        'is_edit': True,
        'edit_staff': staff_member,
        'existing_assignments_json': json.dumps(existing_assignments),
    })


@login_required
def enroll_student_view(request, student_id):
    student = Student.objects.filter(pk=student_id).first()
    if not student:
        messages.error(request, 'Student not found.')
        return redirect('student_list')

    current_session = AcademicSession.objects.filter(is_current=True).first()

    if request.method == 'POST':
        form = EnrollmentForm(request.POST, session=current_session)
        if form.is_valid():
            enrollment = form.save(commit=False)
            enrollment.student = student
            enrollment.academic_year = form.cleaned_data['term'].session.academic_year
            enrollment.save()
            student.classroom = enrollment.classroom
            student.save(update_fields=['classroom'])
            messages.success(request, f"Student {student.first_name} {student.other_names} {student.last_name} successfully enrolled in {enrollment.classroom}!")
            return redirect('student_list')
    else:
        form = EnrollmentForm(session=current_session)

    subjects = Subject.objects.all().order_by('subject_name')

    return render(request, 'sis/enroll_student.html', {
        'student': student,
        'form': form,
        'subjects': subjects,
        'classrooms': ClassRoom.objects.all(),
    })


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")

            if user.is_superuser:
                return redirect('dashboard')

            if user.is_staff or hasattr(user, 'staff_profile'):
                return redirect('dashboard')

            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid credentials. Please try again.')
    else:
        form = AuthenticationForm()

    return render(request, 'sis/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def class_enrollment_portal_view(request):
    if not _is_staff_or_admin(request.user):
        raise PermissionDenied

    staff = getattr(request.user, 'staff_profile', None)
    if request.user.is_superuser:
        classrooms = ClassRoom.objects.all()
    else:
        # Form teachers can only see their own class
        if staff and staff.form_class:
            classrooms = ClassRoom.objects.filter(id=staff.form_class.id)
        else:
            classrooms = ClassRoom.objects.none()
    current_session = AcademicSession.objects.filter(is_current=True).first()
    current_term = Term.objects.filter(is_active=True).first() if current_session else None

    source_class = None
    students_data = []
    promotion_criteria = None
    search_query = request.GET.get('search_query', '').strip()
    source_class_id = request.GET.get('source_class_id')

    if source_class_id:
        source_class = get_object_or_404(ClassRoom, pk=source_class_id)
        criteria_qs = PromotionCriteria.objects.filter(classroom=source_class)
        promotion_criteria = criteria_qs.first()
        min_score = float(promotion_criteria.min_grand_total) if promotion_criteria else 50.00

        term_label = current_term.term_name if current_term else "Term 1"
        term_number = int(term_label.split()[-1])  # "Term 1" -> 1 (SubjectAssessment uses IntegerField)
        year_label = current_session.academic_year if current_session else "2025/2026"

        enrolled_ids = Enrollment.objects.filter(
            classroom=source_class, term=term_label, academic_year=year_label
        ).values_list('student_id', flat=True)

        students = Student.objects.filter(pk__in=enrolled_ids)

        if search_query:
            students = students.filter(
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query) |
                Q(admission_number__icontains=search_query)
            )

        class_subject_names = list(
            ClassSubject.objects.filter(classroom=source_class)
            .values_list('subject__subject_name', flat=True)
        )

        for student in students:
            assessments = SubjectAssessment.objects.filter(
                student=student, term=term_number, academic_year=year_label
            )
            grand_total = sum(a.total_score for a in assessments)
            eligible = grand_total >= min_score

            students_data.append({
                'student': student,
                'grand_total': grand_total,
                'eligible': eligible,
                'subjects': class_subject_names,
            })

        students_data.sort(key=lambda x: x['grand_total'], reverse=True)

    if request.method == 'POST':
        selected_ids = request.POST.getlist('selected_students')
        next_class_id = request.POST.get('next_class_id')
        src_id = request.POST.get('source_class_id')

        if next_class_id and src_id:
            next_class = get_object_or_404(ClassRoom, pk=next_class_id)
            src_class = get_object_or_404(ClassRoom, pk=src_id)

            term_label = current_term.term_name if current_term else "Term 1"
            year_label = current_session.academic_year if current_session else "2025/2026"

            source_ids = set(
                Enrollment.objects.filter(
                    classroom=src_class, term=term_label, academic_year=year_label
                ).values_list('student_id', flat=True)
            )
            selected_set = set(int(sid) for sid in selected_ids)
            held_back_ids = source_ids - selected_set

            for sid in selected_set:
                student = get_object_or_404(Student, pk=sid)
                Enrollment.objects.update_or_create(
                    student=student,
                    term=term_label,
                    academic_year=year_label,
                    defaults={'classroom': next_class},
                )
                student.classroom = next_class
                student.save(update_fields=['classroom'])

            for sid in held_back_ids:
                student = get_object_or_404(Student, pk=sid)
                Enrollment.objects.update_or_create(
                    student=student,
                    term=term_label,
                    academic_year=year_label,
                    defaults={'classroom': src_class},
                )
                student.classroom = src_class
                student.save(update_fields=['classroom'])

            messages.success(
                request,
                "Successfully processed promotions/enrollments for the selected cohort."
            )
            return redirect('class_enrollment_portal')

    context = {
        'classrooms': classrooms,
        'current_session': current_session,
        'current_term': current_term,
        'source_class': source_class,
        'promotion_criteria': promotion_criteria,
        'students_data': students_data,
        'search_query': search_query,
    }
    return render(request, 'sis/class_enrollment_portal.html', context)


@login_required
def configure_session_view(request):
    if not _is_admin(request.user):
        raise PermissionDenied

    sessions = AcademicSession.objects.all()
    terms = Term.objects.all()

    if request.method == 'POST':
        if 'create_new_session' in request.POST:
            year_string = request.POST.get('new_academic_year', '').strip()
            term_name = request.POST.get('new_term_name', '').strip()

            if year_string and term_name:
                session, created = AcademicSession.objects.get_or_create(
                    academic_year=year_string
                )
                AcademicSession.objects.update(is_current=False)
                session.is_current = True
                session.save()

                term_obj, term_created = Term.objects.get_or_create(
                    session=session, term_name=term_name
                )
                Term.objects.update(is_active=False)
                term_obj.is_active = True
                term_obj.save()

                messages.success(request, f"Academic session '{year_string}' created and activated with {term_name}.")
            else:
                messages.error(request, "Both academic year and term are required.")

            return redirect('configure_session')

        session_id = request.POST.get('academic_session')
        term_id = request.POST.get('term')

        if session_id:
            AcademicSession.objects.update(is_current=False)
            selected_session = get_object_or_404(AcademicSession, pk=session_id)
            selected_session.is_current = True
            selected_session.save()

        if term_id:
            Term.objects.update(is_active=False)
            selected_term = get_object_or_404(Term, pk=term_id)
            selected_term.is_active = True
            selected_term.save()

        messages.success(request, "Academic environment successfully updated!")
        return redirect('configure_session')

    context = {
        'sessions': sessions,
        'terms': terms,
        'current_session': AcademicSession.objects.filter(is_current=True).first(),
        'current_term': Term.objects.filter(is_active=True).first(),
    }
    return render(request, 'sis/configure_session.html', context)


@login_required
def global_search_view(request):
    q = request.GET.get('q', '').strip()
    if len(q) < 2:
        return JsonResponse({'results': []})

    full_name_q = Q(first_name__icontains=q) | Q(last_name__icontains=q)

    students = Student.objects.filter(
        full_name_q | Q(admission_number__icontains=q)
    )[:5]

    staff = StaffProfile.objects.filter(
        Q(first_name__icontains=q) | Q(last_name__icontains=q) | Q(staff_id__icontains=q)
    )[:5]

    results = []
    for s in students:
        results.append({
            'id': s.id,
            'name': f"{s.first_name} {s.last_name} ({s.admission_number})",
            'type': 'Student',
            'url': reverse('student_list'),
        })
    for st in staff:
        results.append({
            'id': st.id,
            'name': f"{st.first_name} {st.last_name} ({st.staff_id})",
            'type': 'Staff',
            'url': reverse('staff_detail', args=[st.id]),
        })

    return JsonResponse({'results': results})


@login_required
def compile_grades_view(request):
    if not _is_staff_or_admin(request.user):
        raise PermissionDenied
    staff = getattr(request.user, 'staff_profile', None)
    if request.user.is_superuser:
        classrooms = ClassRoom.objects.all()
    else:
        assigned_class_ids = StaffClassSubject.objects.filter(staff=staff).values_list('classroom_id', flat=True).distinct()
        classrooms = ClassRoom.objects.filter(id__in=assigned_class_ids)

    selected_class_id = request.GET.get('class_id')
    selected_subject_id = request.GET.get('subject_id')
    assessment_type = request.GET.get('assessment_type', 'class_score')
    selected_subject = None
    classroom = None
    students = []
    available_subjects = Subject.objects.none()

    if selected_class_id:
        classroom = get_object_or_404(ClassRoom, pk=selected_class_id)
        students = Student.objects.filter(enrollments__classroom=classroom).distinct()
        available_subjects = Subject.objects.filter(offered_in_classes__classroom=classroom).distinct()
        if not request.user.is_superuser and staff:
            assigned_subject_ids = StaffClassSubject.objects.filter(staff=staff, classroom=classroom).values_list('subject_id', flat=True).distinct()
            available_subjects = available_subjects.filter(id__in=assigned_subject_ids)

        if selected_subject_id:
            selected_subject = get_object_or_404(Subject, pk=selected_subject_id)

    current_session = AcademicSession.objects.filter(is_current=True).first()
    current_term = Term.objects.filter(is_active=True).first()

    if request.method == 'POST':
        selected_class_id = request.POST.get('class_id')
        selected_subject_id = request.POST.get('subject_id')
        classroom = get_object_or_404(ClassRoom, pk=selected_class_id)
        selected_subject = get_object_or_404(Subject, pk=selected_subject_id)
        students = Student.objects.filter(enrollments__classroom=classroom).distinct()

        for student in students:
            cs = request.POST.get(f'cs_{student.id}')
            es = request.POST.get(f'es_{student.id}')
            if cs or es:
                SubjectAssessment.objects.update_or_create(
                    student=student,
                    subject=selected_subject,
                    academic_session=current_session,
                    academic_term=current_term,
                    defaults={
                        'class_score': cs or 0,
                        'exam_score': es or 0,
                        'term': current_term.term_name.split()[-1] if current_term else 1,
                        'academic_year': current_session.academic_year if current_session else '2025/2026',
                    }
                )
        messages.success(request, f'Grades for {selected_subject.subject_name} saved successfully!')
        return redirect(request.path + '?class_id=' + str(selected_class_id) + '&subject_id=' + str(selected_subject_id) + '&assessment_type=' + str(assessment_type))

    grades_matrix = []
    if selected_subject:
        for student in students:
            assessment = SubjectAssessment.objects.filter(
                student=student, subject=selected_subject, academic_session=current_session, academic_term=current_term
            ).first()
            grades_matrix.append({
                'student': student,
                'class_score': assessment.class_score if assessment else '',
                'exam_score': assessment.exam_score if assessment else '',
            })

    context = {
        'classrooms': classrooms,
        'available_subjects': available_subjects,
        'students': students,
        'selected_class': classroom,
        'selected_subject': selected_subject,
        'selected_class_id': selected_class_id,
        'selected_subject_id': selected_subject_id,
        'assessment_type': assessment_type,
        'grades_matrix': grades_matrix,
    }
    return render(request, 'sis/compile_grades.html', context)


@login_required
def midterm_summary_view(request):
    if not _is_staff_or_admin(request.user):
        raise PermissionDenied

    staff = getattr(request.user, 'staff_profile', None)
    classrooms = ClassRoom.objects.none()
    if request.user.is_superuser:
        classrooms = ClassRoom.objects.all()
    elif staff:
        assigned_ids = StaffClassSubject.objects.filter(staff=staff).values_list('classroom_id', flat=True).distinct()
        classrooms = ClassRoom.objects.filter(id__in=assigned_ids)

    selected_class_id = request.GET.get('class_id')
    current_subject_id = request.GET.get('subject_id')

    if selected_class_id and not selected_class_id.isdigit():
        selected_class_id = None
    if current_subject_id and not current_subject_id.isdigit():
        current_subject_id = None

    staff_profile = getattr(request.user, 'staff_profile', None)

    classroom = None
    students = Student.objects.none()
    assigned_subjects = Subject.objects.none()
    report_data = []
    has_records = False

    if selected_class_id:
        classroom = get_object_or_404(ClassRoom, pk=selected_class_id)

        if request.user.is_superuser:
            assigned_subjects = Subject.objects.filter(
                assigned_teachers__classroom_id=selected_class_id
            ).distinct()
        elif staff_profile:
            assigned_subjects = Subject.objects.filter(
                assigned_teachers__staff=staff_profile,
                assigned_teachers__classroom_id=selected_class_id
            ).distinct()

        students = Student.objects.filter(enrollments__classroom=classroom).distinct()

        current_session = AcademicSession.objects.filter(is_current=True).first()
        current_term = Term.objects.filter(is_active=True).first()

        for student in students:
            records = MidTermRecord.objects.filter(student=student, classroom=classroom)
            if current_session:
                records = records.filter(academic_session=current_session)
            if current_term:
                records = records.filter(term=current_term)
            if current_subject_id:
                records = records.filter(subject_id=current_subject_id)

            first_record = records.first()
            midterm_score = (
                f"{first_record.midterm_score:.1f}"
                if first_record and first_record.midterm_score is not None
                else None
            )
            total = sum(
                r.midterm_score for r in records if r.midterm_score is not None
            )
            row = {
                'student': student,
                'midterm_score': midterm_score,
                'total': total,
            }
            report_data.append(row)

        has_records = bool(
            report_data and any(
                row['midterm_score'] is not None or row['total'] > 0
                for row in report_data
            )
        )
        report_data.sort(key=lambda x: x['total'], reverse=True)
        for idx, row in enumerate(report_data):
            row['rank'] = idx + 1

    try:
        user_form_class = request.user.staff_profile.form_class
    except AttributeError:
        user_form_class = None

    context = {
        'classrooms': classrooms,
        'classroom': classroom,
        'selected_class_id': selected_class_id,
        'assigned_subjects': assigned_subjects,
        'current_subject_id': (
            int(current_subject_id)
            if current_subject_id and current_subject_id.isdigit()
            else None
        ),
        'students': students,
        'report_data': report_data,
        'has_records': has_records,
        'user_form_class': user_form_class,
    }
    return render(request, 'sis/midterm_summary.html', context)


@login_required
def compile_midterm_grades_view(request):
    if not _is_staff_or_admin(request.user):
        raise PermissionDenied

    staff = getattr(request.user, 'staff_profile', None)

    if request.user.is_superuser:
        classrooms = ClassRoom.objects.all()
    else:
        assigned_ids = StaffClassSubject.objects.filter(staff=staff).values_list('classroom_id', flat=True).distinct()
        classrooms = ClassRoom.objects.filter(id__in=assigned_ids)

    subjects = Subject.objects.none()
    selected_class_id = request.GET.get('class_id')
    students = []

    if selected_class_id:
        classroom = get_object_or_404(ClassRoom, pk=selected_class_id)
        students = Student.objects.filter(enrollments__classroom=classroom).distinct()

        subject_qs = Subject.objects.filter(offered_in_classes__classroom=classroom).distinct()
        if not request.user.is_superuser and staff:
            assigned_subject_ids = StaffClassSubject.objects.filter(staff=staff, classroom=classroom).values_list('subject_id', flat=True).distinct()
            subject_qs = subject_qs.filter(id__in=assigned_subject_ids)
        subjects = subject_qs
    else:
        classroom = None

    if request.method == 'POST':
        class_id = request.POST.get('class_id')
        classroom = get_object_or_404(ClassRoom, pk=class_id)
        students = Student.objects.filter(enrollments__classroom=classroom).distinct()

        subject_qs = Subject.objects.filter(offered_in_classes__classroom=classroom).distinct()
        if not request.user.is_superuser and staff:
            assigned_subject_ids = StaffClassSubject.objects.filter(staff=staff, classroom=classroom).values_list('subject_id', flat=True).distinct()
            subject_qs = subject_qs.filter(id__in=assigned_subject_ids)

        current_session = AcademicSession.objects.filter(is_current=True).first()
        current_term = Term.objects.filter(is_active=True).first()

        for student in students:
            for subject in subject_qs:
                score_key = f'score_{student.id}_{subject.id}'
                val = request.POST.get(score_key)
                if val:
                    MidTermRecord.objects.update_or_create(
                        student=student,
                        academic_session=current_session,
                        term=current_term,
                        subject=subject,
                        defaults={
                            'classroom': classroom,
                            'midterm_score': val,
                            'recorded_by': staff,
                        }
                    )

        messages.success(request, 'Mid-term grades saved successfully!')
        return redirect(request.path + '?class_id=' + str(class_id))

    grades_matrix = []
    current_session = AcademicSession.objects.filter(is_current=True).first()
    current_term = Term.objects.filter(is_active=True).first()

    for student in students:
        cells = []
        for subject in subjects:
            rec = MidTermRecord.objects.filter(
                student=student,
                academic_session=current_session,
                term=current_term,
                subject=subject,
            ).first()
            cells.append({
                'subject': subject,
                'midterm_score': rec.midterm_score if rec else '',
            })
        grades_matrix.append({'student': student, 'cells': cells})

    context = {
        'classrooms': classrooms,
        'subjects': subjects,
        'students': students,
        'selected_class': classroom,
        'grades_matrix': grades_matrix,
    }
    return render(request, 'sis/compile_midterm_grades.html', context)


@login_required
def api_class_subjects(request):
    class_id = request.GET.get('class_id')
    if not class_id:
        return JsonResponse({'subjects': []})
    mappings = ClassSubject.objects.filter(classroom_id=class_id).select_related('subject')
    subjects_list = []
    for m in mappings:
        existing = StaffClassSubject.objects.filter(
            classroom_id=class_id,
            subject=m.subject
        ).select_related('staff__user').first()
        is_assigned = existing is not None
        assigned_teacher_name = None
        if is_assigned:
            assigned_teacher_name = existing.staff.user.get_full_name() if existing.staff.user else f"{existing.staff.first_name} {existing.staff.last_name}"
        subjects_list.append({
            'id': m.subject.id,
            'name': m.subject.subject_name,
            'is_assigned': is_assigned,
            'assigned_teacher_name': assigned_teacher_name,
        })
    return JsonResponse({'subjects': subjects_list})


@login_required
def api_class_details(request, class_id):
    classroom = get_object_or_404(ClassRoom, pk=class_id)
    student_count = Student.objects.filter(enrollments__classroom=classroom).distinct().count()
    form_teacher_name = ''
    if classroom.form_teacher:
        ft = classroom.form_teacher
        form_teacher_name = f"{ft.first_name} {ft.last_name}".strip()

    subjects_data = []
    scs_qs = StaffClassSubject.objects.filter(classroom=classroom).select_related('subject', 'staff__user')
    for scs in scs_qs:
        teacher_name = ''
        if scs.staff:
            teacher_name = f"{scs.staff.first_name} {scs.staff.last_name}".strip()
        subjects_data.append({
            'name': scs.subject.subject_name,
            'teacher': teacher_name or 'Unassigned',
        })

    return JsonResponse({
        'id': classroom.id,
        'name': classroom.class_name,
        'student_count': student_count,
        'form_teacher': form_teacher_name or 'Unassigned',
        'subjects': subjects_data,
    })


@login_required
def api_subject_details(request, subject_id):
    subject = get_object_or_404(Subject, pk=subject_id)
    scs_qs = StaffClassSubject.objects.filter(subject=subject).select_related('classroom', 'staff__user')

    teacher_names = set()
    class_allocations = []
    for scs in scs_qs:
        teacher_name = ''
        if scs.staff:
            teacher_name = f"{scs.staff.first_name} {scs.staff.last_name}".strip()
        if teacher_name:
            teacher_names.add(teacher_name)
        class_allocations.append({
            'class_name': scs.classroom.class_name,
            'teacher': teacher_name or 'Unassigned',
        })

    return JsonResponse({
        'id': subject.id,
        'name': subject.subject_name,
        'category': 'General Education',
        'classes_count': len(class_allocations),
        'assigned_teachers': sorted(teacher_names),
        'class_allocations': class_allocations,
    })


@login_required
def verify_class_rankings_view(request, class_id):
    if not _is_staff_or_admin(request.user):
        raise PermissionDenied

    classroom = get_object_or_404(ClassRoom, pk=class_id)

    staff = getattr(request.user, 'staff_profile', None)
    is_form_teacher = staff and staff.form_class == classroom

    if not is_form_teacher and not _is_admin(request.user):
        messages.error(request, 'Only the form teacher of this class can verify rankings.')
        return redirect('class_report', class_id=class_id)

    students = Student.objects.filter(enrollments__classroom=classroom).distinct()

    current_session = AcademicSession.objects.filter(is_current=True).first()
    current_term = Term.objects.filter(is_active=True).first()

    report_data = []
    for student in students:
        assessments = SubjectAssessment.objects.filter(student=student, academic_session=current_session, academic_term=current_term)
        grand_total = sum(ast.total_score for ast in assessments)
        report_data.append({
            'student': student,
            'assessments': assessments,
            'grand_total': grand_total,
        })

    report_data = sorted(report_data, key=lambda x: x['grand_total'], reverse=True)
    for index, row in enumerate(report_data):
        row['rank'] = index + 1

    verification = GradeVerification.objects.filter(
        classroom=classroom, academic_session=current_session, academic_term=current_term
    ).first()

    if request.method == 'POST':
        if not verification:
            term_number = int(current_term.term_name.split()[-1]) if current_term else 1
            year_label = current_session.academic_year if current_session else "2025/2026"
            GradeVerification.objects.create(
                classroom=classroom,
                verified_by=staff,
                term=term_number,
                academic_year=year_label,
                academic_session=current_session,
                academic_term=current_term,
            )
            messages.success(request, f'Rankings for {classroom.class_name} verified successfully.')
        else:
            messages.info(request, 'Rankings were already verified for this term.')
        return redirect('class_report', class_id=class_id)

    has_graded_records = any(row['assessments'].exists() for row in report_data)

    return render(request, 'sis/class_report.html', {
        'classroom': classroom,
        'report_data': report_data,
        'is_form_teacher': is_form_teacher,
        'verification': verification,
        'has_graded_records': has_graded_records,
    })


@login_required
def view_account(request):
    staff_profile = getattr(request.user, 'staff_profile', None)
    subjects_with_classes = []
    my_students = []

    if staff_profile:
        assignments = StaffClassSubject.objects.filter(staff=staff_profile).select_related('classroom', 'subject')
        subjects_with_classes = assignments

        if staff_profile.form_class:
            my_students = Student.objects.filter(classroom=staff_profile.form_class).order_by('first_name')
        else:
            class_ids = assignments.values_list('classroom_id', flat=True).distinct()
            my_students = Student.objects.filter(classroom_id__in=class_ids).order_by('first_name') if class_ids else []

    return render(request, 'sis/account.html', {
        'staff_profile': staff_profile,
        'subjects_with_classes': subjects_with_classes,
        'my_students': my_students,
    })


@login_required
def parents_list(request):
    user = request.user

    if user.is_superuser:
        parents = Parent.objects.all().order_by('name')
    elif hasattr(user, 'staff_profile'):
        staff = user.staff_profile
        classroom_ids = StaffClassSubject.objects.filter(
            staff=staff
        ).values_list('classroom_id', flat=True).distinct()
        parents = Parent.objects.filter(
            Q(father_of__classroom_id__in=classroom_ids) |
            Q(mother_of__classroom_id__in=classroom_ids)
        ).distinct().order_by('name')
    else:
        parents = Parent.objects.none()

    return render(request, 'sis/parents_list.html', {'parents': parents})


@login_required
def parent_detail_view(request, parent_id):
    parent = get_object_or_404(Parent, pk=parent_id)
    children = list(parent.father_of.all()) + list(parent.mother_of.all())
    return render(request, 'sis/parent_detail.html', {
        'parent': parent,
        'children': children,
    })


@login_required
def parent_edit_view(request, parent_id):
    if not request.user.is_superuser:
        raise PermissionDenied
    parent = get_object_or_404(Parent, pk=parent_id)
    if request.method == 'POST':
        form = ParentForm(request.POST, instance=parent)
        if form.is_valid():
            form.save()
            messages.success(request, f"Parent '{parent.name}' updated successfully!")
            return redirect('parent_detail', parent_id=parent.id)
    else:
        form = ParentForm(instance=parent)
    return render(request, 'sis/parent_edit.html', {
        'form': form,
        'parent': parent,
    })


def classes_subjects_hub(request):
    classes_list = ClassRoom.objects.annotate(
        student_count=Count('students')
    ).order_by('-order')

    unique_subjects = Subject.objects.all().order_by('subject_name')

    return render(request, 'sis/classes_subjects_hub.html', {
        'classes': classes_list,
        'subjects': unique_subjects,
    })


def timetable_hub(request):
    mock_timetable = {
        'class_name': 'JHS 1',
        'slots_count': 5,
        'days_active': 'Mon - Fri',
        'last_updated': 'Just now',
    }
    return render(request, 'sis/timetable_hub.html', {
        'placeholder_timetable': mock_timetable,
    })