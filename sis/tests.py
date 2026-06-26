from django.test import TestCase
from django.urls import reverse

from .forms import StudentRegistrationForm
from .models import ClassRoom, Parent, Student, Subject, SubjectAssessment


class StudentRegistrationTests(TestCase):
    def test_registration_page_renders(self):
        response = self.client.get(reverse("student_registration"))
        self.assertEqual(response.status_code, 200)

    def test_registration_form_has_gender_choices(self):
        form = StudentRegistrationForm()
        self.assertIn(("Male", "Male"), form.fields["gender"].choices)
        self.assertIn(("Female", "Female"), form.fields["gender"].choices)

    def test_class_report_page_renders(self):
        classroom = ClassRoom.objects.create(class_name="JHS 1")
        student = Student.objects.create(
            admission_number="001",
            first_name="Ada",
            last_name="Lovelace",
            gender="Female",
            dob="2000-01-01",
            status="Day",
            current_class=classroom,
        )
        subject = Subject.objects.create(subject_name="Mathematics")
        SubjectAssessment.objects.create(
            student=student,
            subject=subject,
            term=1,
            academic_year="2025-2026",
            class_score=20,
            exam_score=30,
        )

        response = self.client.get(reverse("class_report_card_short", kwargs={"class_id": classroom.id}))
        self.assertEqual(response.status_code, 200)

    def test_parent_can_be_linked_to_student(self):
        classroom = ClassRoom.objects.create(class_name="JHS 2")
        father = Parent.objects.create(
            name="John Doe",
            occupation="Engineer",
            residential_address="Accra",
            email="john@example.com",
            telephone_number="0200000000",
        )
        mother = Parent.objects.create(
            name="Jane Doe",
            occupation="Teacher",
            residential_address="Accra",
            email="jane@example.com",
            telephone_number="0200000001",
        )
        student = Student.objects.create(
            admission_number="002",
            first_name="Ben",
            last_name="Doe",
            gender="Male",
            dob="2001-02-02",
            status="Boarder",
            living_with="Both",
            previous_school_attended="Old School",
            father=father,
            mother=mother,
            current_class=classroom,
        )

        self.assertEqual(student.father.name, "John Doe")
        self.assertEqual(student.mother.name, "Jane Doe")
