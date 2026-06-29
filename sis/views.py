from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from .models import (
    Parent, Student, Subject, SubjectAssessment, ClassRoom, Enrollment,
    AcademicSession, Term, ClassSubject, PromotionCriteria,
)
from .forms import (
    ParentForm, StudentRegistrationForm, StaffRegistrationForm, EnrollmentForm,
    MarkSubmissionForm,
)

# Create your views here.
def student_list_view(request):
    students = Student.objects.all()
    classrooms = ClassRoom.objects.all()
    return render(request, 'sis/student_list.html', {
        'students': students,
        'classrooms': classrooms,
    })

def student_registration_view(request):
    if request.method == 'POST':
        student_form = StudentRegistrationForm(request.POST)
        father_form = ParentForm(request.POST, prefix='father')
        mother_form = ParentForm(request.POST, prefix='mother')

        if student_form.is_valid() and father_form.is_valid() and mother_form.is_valid():
            # Check if any data was actually typed into the father form
            father_data_typed = any(str(father_form.cleaned_data.get(field) or '').strip() for field in father_form.fields)
            father = None
            if father_data_typed:
                # Save only if name or telephone number is provided
                if father_form.cleaned_data.get('name') or father_form.cleaned_data.get('telephone_number'):
                    father = father_form.save()

            # Check if any data was actually typed into the mother form
            mother_data_typed = any(str(mother_form.cleaned_data.get(field) or '').strip() for field in mother_form.fields)
            mother = None
            if mother_data_typed:
                # Save only if name or telephone number is provided
                if mother_form.cleaned_data.get('name') or mother_form.cleaned_data.get('telephone_number'):
                    mother = mother_form.save()

            student = student_form.save(commit=False)
            student.father = father
            student.mother = mother
            student.save()
            return redirect('enroll_student', student_id=student.id)
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


# bulk score processing view
@login_required
def bulk_grade_entry_view(request, class_id, subject_id):
    if not _is_staff_or_admin(request.user):
        raise PermissionDenied
    classroom = ClassRoom.objects.get(pk=class_id)
    students = Student.objects.filter(enrollments__classroom=classroom).distinct()
    subjects = Subject.objects.all().order_by('subject_name')

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
    current_term = 1
    current_academic_year = "2025-2026"

    if request.method == 'POST':
        for student in students:
            # safety grab input values from the raw POST stream using unique field id
            class_val = request.POST.get(f'class_score_{student.id}')
            exam_val = request.POST.get(f'exam_score_{student.id}')
            
            if class_val and exam_val:
                # Create or update the SubjectAssignment record automatically based on the unique combination of student, subject, term, and academic year
                SubjectAssessment.objects.update_or_create(
                    student=student,
                    subject=subject,
                    term=current_term,
                    academic_year=current_academic_year,
                    defaults={
                        'class_score': class_val,
                        'exam_score': exam_val
                    }
                )
        messages.success(request, f"Grades for {subject.subject_name} saved successfully!")
        return redirect('bulk_grade_entry', class_id=class_id, subject_id=subject_id)
    
    # Build up existing data list to repopulate inputs if scores are already entered
    student_marks_matrix = []
    for student in students:
        existing_assessment = SubjectAssessment.objects.filter(
            student=student, subject=subject, term=current_term, academic_year=current_academic_year
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
    students = Student.objects.filter(enrollments__classroom=classroom).distinct()
    
    report_data = []
    for student in students:
        # Fetch all subject scores for this specific student
        assessments = SubjectAssessment.objects.filter(student=student, term=1)
        
        # Calculate Grand Total across all subjects dynamically
        grand_total = sum(ast.total_score for ast in assessments)
        
        report_data.append({
            'student': student,
            'assessments': assessments,
            'grand_total': grand_total,
        })
        
    # Sort students by grand total descending to rank them automatically
    report_data = sorted(report_data, key=lambda x: x['grand_total'], reverse=True)

    # Inject rank integer positions into the sorted data stream
    for index, row in enumerate(report_data):
        row['rank'] = index + 1
    
    classrooms = ClassRoom.objects.all()
    has_graded_records = any(row['assessments'].exists() for row in report_data)

    return render(request, 'sis/class_report.html', {
        'classroom': classroom,
        'report_data': report_data,
        'classrooms': classrooms,
        'has_graded_records': has_graded_records,
    })


def register_staff_view(request):
    if request.method == 'POST':
        form = StaffRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Staff member registered successfully')
            return redirect('student_list')
    else:
        form = StaffRegistrationForm()

    return render(request, 'sis/register_staff.html', {'form': form})


def enroll_student_view(request, student_id):
    student = Student.objects.filter(pk=student_id).first()
    if not student:
        messages.error(request, 'Student not found.')
        return redirect('student_list')

    if request.method == 'POST':
        form = EnrollmentForm(request.POST)
        if form.is_valid():
            enrollment = form.save(commit=False)
            enrollment.student = student
            enrollment.save()
            messages.success(request, f"Student {student.first_name} {student.last_name} successfully enrolled in {enrollment.classroom}!")
            return redirect('student_list')
    else:
        form = EnrollmentForm()

    subjects = Subject.objects.all().order_by('subject_name')

    return render(request, 'sis/enroll_student.html', {
        'student': student,
        'form': form,
        'subjects': subjects,
        'classrooms': ClassRoom.objects.all(),
    })


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if user.is_superuser:
                return redirect('admin:index')
            if user.is_staff or hasattr(user, 'staff_profile'):
                return redirect('student_list')
            return redirect('student_list')
        else:
            messages.error(request, 'Invalid credentials. Please try again.')
    return render(request, 'sis/login.html')


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def class_enrollment_portal_view(request):
    if not _is_staff_or_admin(request.user):
        raise PermissionDenied

    classrooms = ClassRoom.objects.all()
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
                student=student, term=term_label, academic_year=year_label
            )
            grand_total = sum(a.total_score for a in assessments)
            eligible = grand_total >= min_score

            students_data.append({
                'student': student,
                'grand_total': grand_total,
                'eligible': eligible,
                'subjects': class_subject_names,
            })

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

            for sid in held_back_ids:
                student = get_object_or_404(Student, pk=sid)
                Enrollment.objects.update_or_create(
                    student=student,
                    term=term_label,
                    academic_year=year_label,
                    defaults={'classroom': src_class},
                )

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