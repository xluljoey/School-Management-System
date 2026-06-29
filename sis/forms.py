from django import forms
from .models import Parent, Student, SubjectAssessment, StaffProfile, Enrollment, AcademicSession, Term, ClassSubject, PromotionCriteria


class ParentForm(forms.ModelForm):
    class Meta:
        model = Parent
        fields = ['name', 'occupation', 'residential_address', 'email', 'telephone_number']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full Name'}),
            'occupation': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Occupation'}),
            'residential_address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Residential Address'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'}),
            'telephone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Active Mobile Number'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].required = False


class StudentRegistrationForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['admission_number', 'first_name', 'last_name', 'dob', 'gender', 'status', 'living_with', 'previous_school_attended']
        widgets = {
            'admission_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 0202420168'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}),
            'dob': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'gender': forms.Select(choices=Student.GENDER_CHOICES, attrs={'class': 'form-select'}),
            'status': forms.Select(choices=Student.STATUS_CHOICES, attrs={'class': 'form-select'}),
            'living_with': forms.Select(choices=Student.LIVING_WITH_CHOICES, attrs={'class': 'form-select'}),
            'previous_school_attended': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Name of Previous School'}),
        }


class EnrollmentForm(forms.ModelForm):
    class Meta:
        model = Enrollment
        fields = ['classroom', 'term', 'academic_year']
        widgets = {
            'classroom': forms.Select(attrs={'class': 'form-select'}),
            'term': forms.TextInput(attrs={'class': 'form-control'}),
            'academic_year': forms.TextInput(attrs={'class': 'form-control'}),
        }

class MarkSubmissionForm(forms.ModelForm):
    class Meta:
        model = SubjectAssessment
        fields = ['class_score', 'exam_score']
        
        widgets = {
            'class_score': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'min': '0', 'max': '40', 'placeholder': 'SBA /40'}),
            'exam_score': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'min': '0', 'max': '60', 'placeholder': 'Exam /60'}),
        }

class StaffRegistrationForm(forms.ModelForm):
    class Meta:
        model = StaffProfile
        fields = [
            'title', 'full_name', 'staff_id', 'gender', 'dob', 'designation',
            'ssnit_id', 'email', 'employment_type', 'date_of_appointment',
            'year_of_last_promotion', 'department', 'qualification', 'certificate',
            'name_of_institution_completed', 'year_completed', 'form_class', 'subject_areas'
        ]
        widgets = {
            'title': forms.Select(attrs={'class': 'form-select'}),
            'full_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full Name'}),
            'staff_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Staff ID'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'dob': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'designation': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Senior Superintendent'}),
            'ssnit_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'SSNIT ID'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'}),
            'employment_type': forms.Select(attrs={'class': 'form-select'}),
            'date_of_appointment': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'year_of_last_promotion': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Year of Last Promotion'}),
            'department': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Department'}),
            'qualification': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Qualification'}),
            'certificate': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., B.Ed Education'}),
            'name_of_institution_completed': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Institution Completed'}),
            'year_completed': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Year Completed'}),
            'form_class': forms.Select(attrs={'class': 'form-select'}),
            'subject_areas': forms.CheckboxSelectMultiple(),
        }


class AcademicSessionForm(forms.ModelForm):
    class Meta:
        model = AcademicSession
        fields = '__all__'
        widgets = {
            'academic_year': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 2025/2026'}),
        }


class TermForm(forms.ModelForm):
    class Meta:
        model = Term
        fields = '__all__'
        widgets = {
            'session': forms.Select(attrs={'class': 'form-select'}),
            'term_name': forms.Select(attrs={'class': 'form-select'}),
        }


class ClassSubjectForm(forms.ModelForm):
    class Meta:
        model = ClassSubject
        fields = '__all__'
        widgets = {
            'classroom': forms.Select(attrs={'class': 'form-select'}),
            'subject': forms.Select(attrs={'class': 'form-select'}),
        }


class PromotionCriteriaForm(forms.ModelForm):
    class Meta:
        model = PromotionCriteria
        fields = '__all__'
        widgets = {
            'classroom': forms.Select(attrs={'class': 'form-select'}),
            'min_grand_total': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }