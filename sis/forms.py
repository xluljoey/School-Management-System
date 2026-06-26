from django import forms
from .models import Student, SubjectAssessment


class StudentRegistrationForm(forms.ModelForm):
    gender = forms.ChoiceField(
        choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')],
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    class Meta:
        model = Student
        # The fields to show on registration page
        fields = ['admission_number', 'first_name', 'last_name', 'gender', 'dob', 'status', 'current_class']

        # We use widgets to inject Bootstrap layout styling into Django's auto-generated fields
        widgets = {
            'admission_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 0202420168'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}),
            'dob': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'status': forms.Select(choices=[('Day', 'Day'), ('Boarder', 'Boarder')], attrs={'class': 'form-select'}),
            'current_class': forms.Select(attrs={'class': 'form-select'}),
        }

class MarkSubmissionForm(forms.ModelForm):
    class Meta:
        model = SubjectAssessment
        fields = ['class_score', 'exam_score']
        
        widgets = {
            'class_score': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'min': '0', 'max': '40', 'placeholder': 'SBA /40'}),
            'exam_score': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'min': '0', 'max': '60', 'placeholder': 'Exam /60'}),
        }