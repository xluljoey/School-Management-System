from django.test import TestCase
from django.urls import reverse

from .forms import StaffRegistrationForm, StudentRegistrationForm
from .models import ClassRoom, Department, Designation, Parent, Student, Subject, SubjectAssessment, StaffProfile


class StudentRegistrationTests(TestCase):
    def setUp(self):
        from django.contrib.auth.models import User
        self.user = User.objects.create_superuser(username="admin", password="password", email="admin@example.com")
        self.client.login(username="admin", password="password")

    def test_e_path_redirects_to_students(self):
        response = self.client.get("/e")
        self.assertRedirects(response, reverse("student_list"))

    def test_registration_page_renders(self):
        response = self.client.get(reverse("student_registration"))
        self.assertEqual(response.status_code, 200)

    def test_staff_registration_page_renders(self):
        response = self.client.get(reverse("register_staff"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Staff Registration")

    def test_staff_registration_saves_and_redirects(self):
        classroom = ClassRoom.objects.create(class_name="JHS 3")
        subject = Subject.objects.create(subject_name="ICT")
        response = self.client.post(reverse("register_staff"), {
            "title": "Mr.",
            "first_name": "Kwame",
            "last_name": "Boateng",
            "staff_id": "STAFF-001",
            "gender": "Male",
            "dob": "1985-01-01",
            "designation": "Teacher",
            "email": "kwame@example.com",
            "employment_type": "Permanent",
            "date_of_appointment": "2020-01-01",
            "department": "Mathematics",
            "qualification": "Degree",
            "certificate": "B.Ed",
            "name_of_institution_completed": "UCC",
            "year_completed": "2020",
            "form_class": classroom.id,
            "subject_areas": [subject.id],
        })
        self.assertEqual(response.status_code, 302)
        staff = StaffProfile.objects.get(staff_id="STAFF-001")
        self.assertEqual(f"{staff.first_name} {staff.last_name}", "Kwame Boateng")
        self.assertIn(subject, staff.subject_areas.all())

    def test_student_list_renders_with_classrooms(self):
        classroom1 = ClassRoom.objects.create(class_name="JHS 1")
        classroom2 = ClassRoom.objects.create(class_name="JHS 2")
        response = self.client.get(reverse("student_list"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("classrooms", response.context)
        self.assertEqual(len(response.context["classrooms"]), 2)
        self.assertContains(response, "JHS 1")
        self.assertContains(response, "JHS 2")

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

    def test_parent_form_fields_optional(self):
        from .forms import ParentForm
        form = ParentForm()
        for field_name, field in form.fields.items():
            self.assertFalse(field.required, f"Field {field_name} should be optional")

    def test_register_student_no_parents(self):
        classroom = ClassRoom.objects.create(class_name="Class A")
        post_data = {
            "admission_number": "1001",
            "first_name": "Child",
            "last_name": "One",
            "dob": "2015-05-05",
            "gender": "Male",
            "status": "Day",
            "living_with": "Both",
            "previous_school_attended": "None",
            "current_class": classroom.id,
            # Father details (empty)
            "father-name": "",
            "father-occupation": "",
            "father-residential_address": "",
            "father-email": "",
            "father-telephone_number": "",
            # Mother details (empty)
            "mother-name": "",
            "mother-occupation": "",
            "mother-residential_address": "",
            "mother-email": "",
            "mother-telephone_number": "",
        }
        response = self.client.post(reverse("student_registration"), post_data)
        self.assertEqual(response.status_code, 302) # Redirects to student_list
        student = Student.objects.get(admission_number="1001")
        self.assertIsNone(student.father)
        self.assertIsNone(student.mother)

    def test_register_student_only_mother(self):
        classroom = ClassRoom.objects.create(class_name="Class B")
        post_data = {
            "admission_number": "1002",
            "first_name": "Child",
            "last_name": "Two",
            "dob": "2015-05-05",
            "gender": "Female",
            "status": "Day",
            "living_with": "Mother",
            "previous_school_attended": "None",
            "current_class": classroom.id,
            # Father details (empty)
            "father-name": "",
            "father-occupation": "",
            "father-residential_address": "",
            "father-email": "",
            "father-telephone_number": "",
            # Mother details (filled)
            "mother-name": "Jane Mother",
            "mother-occupation": "Engineer",
            "mother-residential_address": "Home Address",
            "mother-email": "jane@example.com",
            "mother-telephone_number": "0241234567",
        }
        response = self.client.post(reverse("student_registration"), post_data)
        self.assertEqual(response.status_code, 302)
        student = Student.objects.get(admission_number="1002")
        self.assertIsNone(student.father)
        self.assertIsNotNone(student.mother)
        self.assertEqual(student.mother.name, "Jane Mother")
        self.assertEqual(student.mother.telephone_number, "0241234567")

    def test_register_student_parent_missing_name_and_phone(self):
        classroom = ClassRoom.objects.create(class_name="Class C")
        post_data = {
            "admission_number": "1003",
            "first_name": "Child",
            "last_name": "Three",
            "dob": "2015-05-05",
            "gender": "Male",
            "status": "Day",
            "living_with": "Both",
            "previous_school_attended": "None",
            "current_class": classroom.id,
            # Father details (occupation only - no name/phone)
            "father-name": "",
            "father-occupation": "Doctor",
            "father-residential_address": "",
            "father-email": "",
            "father-telephone_number": "",
            # Mother details (empty)
            "mother-name": "",
            "mother-occupation": "",
            "mother-residential_address": "",
            "mother-email": "",
            "mother-telephone_number": "",
        }
        response = self.client.post(reverse("student_registration"), post_data)
        self.assertEqual(response.status_code, 302)
        student = Student.objects.get(admission_number="1003")
        self.assertIsNone(student.father)
        self.assertIsNone(student.mother)

    def test_register_student_parent_only_phone(self):
        classroom = ClassRoom.objects.create(class_name="Class D")
        post_data = {
            "admission_number": "1004",
            "first_name": "Child",
            "last_name": "Four",
            "dob": "2015-05-05",
            "gender": "Female",
            "status": "Day",
            "living_with": "Both",
            "previous_school_attended": "None",
            "current_class": classroom.id,
            # Father details (telephone only)
            "father-name": "",
            "father-occupation": "",
            "father-residential_address": "",
            "father-email": "",
            "father-telephone_number": "0509999999",
            # Mother details (empty)
            "mother-name": "",
            "mother-occupation": "",
            "mother-residential_address": "",
            "mother-email": "",
            "mother-telephone_number": "",
        }
        response = self.client.post(reverse("student_registration"), post_data)
        self.assertEqual(response.status_code, 302)
        student = Student.objects.get(admission_number="1004")
        self.assertIsNotNone(student.father)
        self.assertIsNone(student.mother)
        self.assertEqual(student.father.telephone_number, "0509999999")

    def test_bulk_grade_entry_saves_and_redirects_to_same_view(self):
        classroom = ClassRoom.objects.create(class_name="Class E")
        subject = Subject.objects.create(subject_name="Science")
        student = Student.objects.create(
            admission_number="1005",
            first_name="Alice",
            last_name="Test",
            dob="2010-01-01",
            gender="Female",
            status="Day",
            current_class=classroom,
        )
        post_data = {
            f"class_score_{student.id}": "25.5",
            f"exam_score_{student.id}": "45.0",
        }
        url = reverse("bulk_grade_entry", kwargs={"class_id": classroom.id, "subject_id": subject.id})
        response = self.client.post(url, post_data)
        
        # Verify it redirects to the same bulk grade entry view
        self.assertRedirects(response, url)
        
        # Verify assessment was saved correctly
        assessment = SubjectAssessment.objects.get(student=student, subject=subject)
        self.assertEqual(float(assessment.class_score), 25.5)
        self.assertEqual(float(assessment.exam_score), 45.0)

        # Verify messages contains the success message
        messages_list = list(response.wsgi_request._messages)
        self.assertEqual(len(messages_list), 1)
        self.assertEqual(str(messages_list[0]), f"Grades for Science saved successfully!")

    def test_class_report_empty_state_displays_banner(self):
        classroom = ClassRoom.objects.create(class_name="Class Empty")
        url = reverse("class_report", kwargs={"class_id": classroom.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("classrooms", response.context)
        self.assertFalse(response.context["has_graded_records"])
        self.assertContains(response, "No student grade records compiled for this class yet.")

    def test_class_report_with_grades_displays_table(self):
        classroom = ClassRoom.objects.create(class_name="Class Graded")
        student = Student.objects.create(
            admission_number="1006",
            first_name="Evelyn",
            last_name="Standings",
            dob="2010-01-01",
            gender="Female",
            status="Day",
            current_class=classroom,
        )
        subject = Subject.objects.create(subject_name="English")
        SubjectAssessment.objects.create(
            student=student,
            subject=subject,
            term=1,
            academic_year="2025-2026",
            class_score=30,
            exam_score=50,
        )
        url = reverse("class_report", kwargs={"class_id": classroom.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["has_graded_records"])
        self.assertContains(response, "Evelyn Standings")
        self.assertNotContains(response, "No student grade records compiled for this class yet.")
