from datetime import date

from django.db import models
from django.contrib.auth.models import User

class ClassRoom(models.Model):
    class_name = models.CharField(max_length=50, unique =True)

    def __str__(self):
        return self.class_name
    
class Subject(models.Model):
    subject_name = models.CharField(max_length=100, unique =True)

    def __str__(self):
        return self.subject_name
    
class StaffProfile(models.Model):
    TITLE_CHOICES = [
        ('Mr.', 'Mr.'),
        ('Mrs.', 'Mrs.'),
        ('Ms.', 'Ms.'),
        ('Dr.', 'Dr.'),
        ('Rev.', 'Rev.'),
    ]
    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
    ]
    EMPLOYMENT_CHOICES = [
        ('Permanent', 'Permanent'),
        ('Contract', 'Contract'),
    ]

    title = models.CharField(max_length=20, choices=TITLE_CHOICES, default='Mr.')
    full_name = models.CharField(max_length=255, default='')
    staff_id = models.CharField(max_length=50, unique=True, default='')
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='staff_profile', null=True, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default='Male')
    dob = models.DateField(verbose_name="Date of Birth", default=date.today)
    designation = models.CharField(max_length=100, default='')
    ssnit_id = models.CharField(max_length=50, blank=True, null=True, verbose_name="SSNIT ID")
    email = models.EmailField(unique=True)
    employment_type = models.CharField(max_length=50, choices=EMPLOYMENT_CHOICES, default='Permanent')
    date_of_appointment = models.DateField(default=date.today)
    year_of_last_promotion = models.IntegerField(blank=True, null=True)
    department = models.CharField(max_length=100, default='')
    qualification = models.CharField(max_length=150, default='')
    certificate = models.CharField(max_length=150, default='')
    name_of_institution_completed = models.CharField(max_length=255, default='')
    year_completed = models.IntegerField(default=2000)

    form_class = models.OneToOneField('ClassRoom', on_delete=models.SET_NULL, null=True, blank=True, related_name='form_teacher')
    subject_areas = models.ManyToManyField('Subject', related_name='teachers', help_text="Select all subjects this staff member is assigned to teach.")

    def __str__(self):
        return f"{self.title} {self.full_name}"
    
class Parent(models.Model):
    name = models.CharField(max_length=255, blank=True, null=True)
    occupation = models.CharField(max_length=150, blank=True, null=True)
    residential_address = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    telephone_number = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return self.name or "Unnamed Parent"


class Student(models.Model):
    GENDER_CHOICES = [('Male', 'Male'), ('Female', 'Female')]
    STATUS_CHOICES = [('Day', 'Day'), ('Boarder', 'Boarder')]
    LIVING_WITH_CHOICES = [('Mother', 'Mother'), ('Father', 'Father'), ('Both', 'Both')]

    admission_number = models.CharField(max_length=50, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    dob = models.DateField(verbose_name='Date of Birth')
    date_of_admission = models.DateField(default=date.today)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    living_with = models.CharField(max_length=10, choices=LIVING_WITH_CHOICES, default='Both')
    previous_school_attended = models.CharField(max_length=255, default='N/A')
    father = models.ForeignKey(Parent, on_delete=models.SET_NULL, null=True, blank=True, related_name='father_of')
    mother = models.ForeignKey(Parent, on_delete=models.SET_NULL, null=True, blank=True, related_name='mother_of')
    current_class = models.ForeignKey(ClassRoom, on_delete=models.PROTECT)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.admission_number})"


class SubjectAssessment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    subject = models.ForeignKey('Subject', on_delete=models.CASCADE)
    term = models.IntegerField()
    academic_year = models.CharField(max_length=9)
    class_score = models.DecimalField(max_digits=5, decimal_places=2)
    exam_score = models.DecimalField(max_digits=5, decimal_places=2)

    @property
    def total_score(self):
        return float(self.class_score or 0) + float(self.exam_score or 0)

    @property
    def grade_and_remark(self):
        total = self.total_score
        if total >= 80:
            return ("1", "Highest Distinction")
        elif total >= 75:
            return ("2", "Distinction")
        elif total >= 70:
            return ("3", "Excellent")
        elif total >= 65:
            return ("4", "Very Good")
        elif total >= 60:
            return ("5", "Good")
        elif total >= 55:
            return ("6", "Credit")
        elif total >= 50:
            return ("7", "Satisfactory")
        elif total >= 40:
            return ("8", "Pass")
        return ("9", "Fail")

    def __str__(self):
        return f"Assessment for {self.student}"


class SubjectAssignment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    term = models.IntegerField() # 1, 2, or 3
    academic_year = models.CharField(max_length=9) # e.g., "2025-2026"
    class_score = models.DecimalField(max_digits=5, decimal_places=2) # Out of 30/40
    exam_score = models.DecimalField(max_digits=5, decimal_places=2) # Out of 60/70

    @property
    def total_score(self):
        """Adds class score and exam score together dynamically."""
        return float(self.class_score or 0) + float(self.exam_score or 0)

    @property
    def grade_and_remark(self):
        """Returns standard Ghanaian basic school grading tier (1 to 9)."""
        total = self.total_score
        if total >= 80: return ("1", "Highest Distinction")
        elif total >= 75: return ("2", "Distinction")
        elif total >= 70: return ("3", "Excellent")
        elif total >= 65: return ("4", "Very Good")
        elif total >= 60: return ("5", "Good")
        elif total >= 55: return ("6", "Credit")
        elif total >= 50: return ("7", "Satisfactory")
        elif total >= 40: return ("8", "Pass")
        else: return ("9", "Fail")



# Create your models here.
