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
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    staff_id = models.CharField(max_length=50, primary_key=True)
    title = models.CharField(max_length=20)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    gender = models.CharField(max_length=10)
    dob = models.DateField()
    designation = models.CharField(max_length=100)
    subjects_taught = models.ManyToManyField(Subject, blank=True)
    form_class = models.ForeignKey(ClassRoom, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.title} {self.first_name} {self.last_name}"
    
class Student(models.Model):
    admission_number = models.CharField(max_length=50, unique=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    gender = models.CharField(max_length=10)
    dob = models.DateField()
    status = models.CharField(max_length=20) #Day / Boarder
    current_class = models.ForeignKey(ClassRoom, on_delete=models.PROTECT)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.admisssion_number})"
        
class SubjectAssignment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    term = models.IntegerField() # 1, 2, or 3
    academic_year = models.CharField(max_length=9) # e.g., "2025-2026"
    class_score = models.DecimalField(max_digits=5, decimal_places=2) # Out of 30/40
    exam_score = models.DecimalField(max_digits=5, decimal_places=2) # Out of 60/70




# Create your models here.
