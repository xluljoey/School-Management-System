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
    term = forms.ModelChoiceField(
        queryset=Term.objects.all(),
        empty_label="-- Select Active Term --",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = Enrollment
        fields = ['classroom', 'term']
        widgets = {
            'classroom': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        session = kwargs.pop('session', None)
        super().__init__(*args, **kwargs)
        self.fields['term'].label_from_instance = lambda obj: f"{obj.term_name} ({obj.session.academic_year})"
        if session:
            self.fields['term'].queryset = Term.objects.filter(session=session)

    def save(self, commit=True):
        instance = super().save(commit=False)
        term_obj = self.cleaned_data.get('term')
        if term_obj:
            instance.term = term_obj.term_name
            instance.academic_year = term_obj.session.academic_year
        if commit:
            instance.save()
        return instance

class MarkSubmissionForm(forms.ModelForm):
    class Meta:
        model = SubjectAssessment
        fields = ['class_score', 'exam_score']
        
        widgets = {
            'class_score': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'min': '0', 'max': '40', 'placeholder': 'SBA /40'}),
            'exam_score': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'min': '0', 'max': '60', 'placeholder': 'Exam /60'}),
        }

class StaffRegistrationForm(forms.ModelForm):
    QUALIFICATION_CHOICES = [
        ('Diploma', 'Diploma'),
        ('Degree', 'Bachelors Degree'),
        ('Masters', 'Masters Degree'),
        ('PhD', 'Doctorate (PhD)'),
        ('Other', 'Other'),
    ]
    CERTIFICATE_CHOICES = [
        ('B.Ed', 'B.Ed (Education)'),
        ('B.A', 'B.A (Bachelor of Arts)'),
        ('B.Sc', 'B.Sc (Bachelor of Science)'),
        ('PGDE', 'PGDE (Postgrad Diploma in Ed)'),
        ('M.Ed', 'M.Ed (Master of Education)'),
        ('Other', 'Other'),
    ]

    qualification = forms.ChoiceField(choices=QUALIFICATION_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))
    certificate = forms.ChoiceField(choices=CERTIFICATE_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))

    class Meta:
        model = StaffProfile
        fields = [
            'title', 'full_name', 'staff_id', 'gender', 'dob', 'designation',
            'ssnit_id', 'email', 'employment_type', 'date_of_appointment',
            'year_of_last_promotion', 'department', 'qualification', 'certificate',
            'name_of_institution_completed', 'year_completed', 'profile_picture',
            'form_class', 'subject_areas',
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
            'name_of_institution_completed': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Institution Completed'}),
            'year_completed': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Year Completed'}),
            'profile_picture': forms.ClearableFileInput(attrs={'class': 'form-control'}),
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