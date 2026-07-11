from datetime import date
import os
import uuid

from django.db import models
from django.contrib.auth.models import User

class ClassRoom(models.Model):
    class_name = models.CharField(max_length=50, unique=True)
    order = models.PositiveIntegerField(
        default=0,
        help_text="Used to sort classes hierarchically (e.g., Class 1 = 1, JHS 3 = 9)"
    )
    form_master = models.ForeignKey('StaffProfile', on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_class')

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.class_name
    
class Subject(models.Model):
    subject_name = models.CharField(max_length=100, unique =True)

    def __str__(self):
        return self.subject_name
    
class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Designation(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


def get_staff_photo_path(instance, filename):
    ext = filename.split('.')[-1]
    unique_name = instance.staff_id if hasattr(instance, 'staff_id') and instance.staff_id else uuid.uuid4().hex[:10]
    clean_filename = f"{unique_name}.{ext}"
    return os.path.join('uploads/profile_pics/', clean_filename)


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
    first_name = models.CharField(max_length=100, default='')
    last_name = models.CharField(max_length=100, default='')
    other_names = models.CharField(max_length=100, blank=True, null=True, default='')
    #full_name = models.CharField(max_length=255, default='')
    staff_id = models.CharField(max_length=50, unique=True, default='')
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='staff_profile', null=True, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default='Male')
    dob = models.DateField(verbose_name="Date of Birth", default=date.today)
    designation = models.ForeignKey(Designation, on_delete=models.SET_NULL, null=True, blank=True)
    ssnit_id = models.CharField(max_length=50, blank=True, null=True, verbose_name="SSNIT ID")
    phone_number = models.CharField(max_length=15, blank=True, null=True, verbose_name="Phone Number")
    email = models.EmailField(unique=True)
    employment_type = models.CharField(max_length=50, choices=EMPLOYMENT_CHOICES, default='Permanent')
    date_of_appointment = models.DateField(default=date.today)
    year_of_last_promotion = models.IntegerField(blank=True, null=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    qualification = models.CharField(max_length=150, default='')
    certificate = models.CharField(max_length=150, default='')
    name_of_institution_completed = models.CharField(max_length=255, default='')
    year_completed = models.IntegerField(default=2000)
    profile_picture = models.ImageField(upload_to=get_staff_photo_path, max_length=100, blank=True, null=True)
    address = models.TextField(blank=True, null=True, verbose_name="Residential Address")

    form_class = models.OneToOneField('ClassRoom', on_delete=models.SET_NULL, null=True, blank=True, related_name='form_teacher')
    subject_areas = models.ManyToManyField('Subject', blank=True, related_name='teachers', help_text="Select all subjects this staff member is assigned to teach.")

    @property
    def avatar_initial(self):
        for name_part in [self.first_name, self.other_names, self.last_name]:
            if name_part:
                return str(name_part).strip()[0].upper()
        if self.user and self.user.first_name:
            return self.user.first_name[0].upper()
        if hasattr(self, 'full_name') and self.full_name:
            return self.full_name.strip()[0].upper()
        return ""

    @property
    def years_of_experience(self):
        if self.date_of_appointment:
            delta = date.today() - self.date_of_appointment
            return delta.days // 365
        return None

    def __str__(self):
        return f"{self.title} {self.first_name} {self.last_name} {self.other_names or ''} ({self.staff_id})"

class Parent(models.Model):
    name = models.CharField(max_length=255, blank=True, null=True)
    occupation = models.CharField(max_length=150, blank=True, null=True)
    residential_address = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    telephone_number = models.CharField(max_length=20, blank=True, null=True)

    @property
    def full_name(self):
        return self.name

    @full_name.setter
    def full_name(self, value):
        self.name = value

    @property
    def phone(self):
        return self.telephone_number

    @phone.setter
    def phone(self, value):
        self.telephone_number = value

    @property
    def address(self):
        return self.residential_address

    @address.setter
    def address(self, value):
        self.residential_address = value

    def __str__(self):
        return self.name or "Unnamed Parent"


class Student(models.Model):
    GENDER_CHOICES = [('Male', 'Male'), ('Female', 'Female')]
    STATUS_CHOICES = [('Day', 'Day'), ('Boarder', 'Boarder')]
    LIVING_WITH_CHOICES = [('Mother', 'Mother'), ('Father', 'Father'), ('Both', 'Both')]

    admission_number = models.CharField(max_length=50, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    other_names = models.CharField(max_length=100, blank=True, null=True, default='')
    dob = models.DateField(verbose_name='Date of Birth')
    date_of_admission = models.DateField(default=date.today)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    living_with = models.CharField(max_length=10, choices=LIVING_WITH_CHOICES, default='Both')
    previous_school_attended = models.CharField(max_length=255, default='N/A')
    profile_picture = models.ImageField(upload_to='students/profiles/', blank=True, null=True)
    classroom = models.ForeignKey('ClassRoom', on_delete=models.SET_NULL, null=True, blank=True, related_name='students')
    father = models.ForeignKey(Parent, on_delete=models.SET_NULL, null=True, blank=True, related_name='father_of')
    mother = models.ForeignKey(Parent, on_delete=models.SET_NULL, null=True, blank=True, related_name='mother_of')
    
    @property
    def current_class(self):
        """Return the most recent enrolled ClassRoom for this student, or None."""
        latest = self.enrollments.order_by('-date_enrolled').first()
        return latest.classroom if latest else None

    @current_class.setter
    def current_class(self, classroom):
        self._temp_current_class = classroom

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if hasattr(self, '_temp_current_class') and self._temp_current_class:
            from .models import Enrollment
            # Find current active term if available
            from .models import Term, AcademicSession
            current_session = AcademicSession.objects.filter(is_current=True).first()
            current_term = Term.objects.filter(is_active=True).first() if current_session else None
            term_name = current_term.term_name if current_term else "Term 1"
            acad_year = current_session.academic_year if current_session else "2025/2026"
            
            Enrollment.objects.get_or_create(
                student=self,
                classroom=self._temp_current_class,
                term=term_name,
                academic_year=acad_year,
            )
            del self._temp_current_class

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.admission_number})"

    @property
    def get_full_name(self):
        parts = [p for p in [self.first_name, self.other_names, self.last_name] if p]
        return " ".join(parts)
    



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

    class Meta:
        verbose_name = "Student Subject Record"
        verbose_name_plural = "Student Subject Records"

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


class StaffClassSubject(models.Model):
    staff = models.ForeignKey('StaffProfile', on_delete=models.CASCADE, related_name='assigned_classes_subjects')
    classroom = models.ForeignKey('ClassRoom', on_delete=models.CASCADE, related_name='assigned_teachers')
    subject = models.ForeignKey('Subject', on_delete=models.CASCADE, related_name='assigned_teachers')

    class Meta:
        verbose_name = "Teacher Subject Assignment"
        verbose_name_plural = "Teacher Subject Assignments"
        unique_together = ('staff', 'classroom', 'subject')

    def __str__(self):
        return f"{self.staff} -> {self.classroom.class_name} ({self.subject.subject_name})"


class Enrollment(models.Model):
    student = models.ForeignKey('Student', on_delete=models.CASCADE, related_name='enrollments')
    classroom = models.ForeignKey('ClassRoom', on_delete=models.PROTECT, related_name='enrollments')
    term = models.CharField(max_length=20, default="Term 1")
    academic_year = models.CharField(max_length=20, default="2025/2026")
    date_enrolled = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'classroom', 'term', 'academic_year')

    def __str__(self):
        return f"{self.student} -> {self.classroom} ({self.term} {self.academic_year})"


class AcademicSession(models.Model):
    academic_year = models.CharField(max_length=20, unique=True, help_text="e.g., 2025/2026")
    is_current = models.BooleanField(default=False, help_text="True if this is the active academic year")

    def __str__(self):
        return self.academic_year


class Term(models.Model):
    TERM_CHOICES = [
        ('Term 1', 'Term 1'),
        ('Term 2', 'Term 2'),
        ('Term 3', 'Term 3'),
    ]
    session = models.ForeignKey(AcademicSession, on_delete=models.CASCADE, related_name='terms')
    term_name = models.CharField(max_length=20, choices=TERM_CHOICES)
    is_active = models.BooleanField(default=False, help_text="True if this is the active grading term")

    class Meta:
        unique_together = ('session', 'term_name')

    def __str__(self):
        return f"{self.term_name} ({self.session.academic_year})"


class ClassSubject(models.Model):
    classroom = models.ForeignKey(ClassRoom, on_delete=models.CASCADE, related_name='subjects_offered')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='offered_in_classes')

    class Meta:
        unique_together = ('classroom', 'subject')
        verbose_name_plural = 'Class Subjects'

    def __str__(self):
        return f"{self.subject.subject_name} — {self.classroom.class_name}"


class PromotionCriteria(models.Model):
    classroom = models.ForeignKey(ClassRoom, on_delete=models.CASCADE, related_name='promotion_criteria')
    min_grand_total = models.DecimalField(
        max_digits=5, decimal_places=2, default=50.00,
        help_text="Minimum aggregate/grand total score required to qualify for promotion"
    )

    class Meta:
        verbose_name_plural = 'Promotion Criteria'

    def __str__(self):
        return f"{self.classroom.class_name} (min: {self.min_grand_total})"


class GradeVerification(models.Model):
    classroom = models.ForeignKey(ClassRoom, on_delete=models.CASCADE, related_name='grade_verifications')
    verified_by = models.ForeignKey(StaffProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='verifications')
    verified_at = models.DateTimeField(auto_now_add=True)
    term = models.IntegerField()
    academic_year = models.CharField(max_length=9)

    class Meta:
        unique_together = ('classroom', 'term', 'academic_year')
        verbose_name = 'Grade Verification'
        verbose_name_plural = 'Grade Verifications'

    def __str__(self):
        return f"{self.classroom.class_name} - Term {self.term} ({self.academic_year}) verified"


class MidTermRecord(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='midterm_records')
    academic_session = models.ForeignKey(AcademicSession, on_delete=models.CASCADE)
    term = models.ForeignKey(Term, on_delete=models.CASCADE)
    classroom = models.ForeignKey(ClassRoom, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    midterm_score = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    recorded_by = models.ForeignKey(StaffProfile, on_delete=models.SET_NULL, null=True)
    date_recorded = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('student', 'academic_session', 'term', 'subject')
        verbose_name = 'Mid-Term Record'
        verbose_name_plural = 'Mid-Term Records'

    def __str__(self):
        return f"{self.student} — {self.subject} ({self.term})"
