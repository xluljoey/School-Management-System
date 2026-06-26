from django.shortcuts import render, redirect
from .models import Student, Subject, SubjectAssessment, ClassRoom
from .forms import StudentRegistrationForm
from .forms import MarkSubmissionForm

# Create your views here.
def student_list_view(request):
    students = Student.objects.all()
    return render(request, 'sis/student_list.html', {'students': students}) # Add 'sis/' here

def student_registration_view(request):
    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            form.save() #Saves the new student record to the database
            return redirect('student_list') # Redirect to student list page after successful registration
    else:
        form = StudentRegistrationForm()
    return render(request, 'sis/student_registration.html', {'form': form}) # Add 'sis/' here

# bulk score processing view
def bulk_grade_entry_view(request, class_id,subject_id):
    classroom = ClassRoom.objects.get(pk=class_id)
    students = Student.objects.filter(current_class=classroom)
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
        return redirect('student_list')  # Redirect to student list page after successful submission
    
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

def class_report_card_view(request, class_id):
    classroom = ClassRoom.objects.get(pk=class_id)
    students = Student.objects.filter(current_class=classroom)
    
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

    return render(request, 'sis/class_report.html', {'classroom': classroom, 'report_data': report_data})