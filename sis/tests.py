import io

from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
from datetime import date
from unittest.mock import patch

from django.test import RequestFactory, TestCase
from django.urls import reverse

from .forms import StaffRegistrationForm, StudentRegistrationForm
from .models import ClassRoom, Department, Designation, Parent, Student, Subject, SubjectAssessment, StaffProfile, AcademicSession, Term, ClassSubject


class StudentRegistrationTests(TestCase):
    def setUp(self):
        from django.contrib.auth.models import User
        self.user = User.objects.create_superuser(username="admin", password="password", email="admin@example.com")
        self.client.login(username="admin", password="password")

    def test_dashboard_calendar_partial_renders_without_full_page_shell(self):
        from django.contrib.auth.models import User

        user = User.objects.create_user(username="staff", password="password", email="staff@example.com")
        self.client.login(username="staff", password="password")

        response = self.client.get(reverse("dashboard"), {"month": 7, "year": 2026, "calendar_partial": 1})

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "sis/partials/dashboard_calendar.html")
        self.assertNotContains(response, "<!DOCTYPE html>")
        self.assertContains(response, "Calendar")

    def test_dashboard_calendar_marks_today_in_current_month(self):
        from .views import _build_dashboard_calendar_data

        request = RequestFactory().get(reverse("dashboard"))
        request.user = self.user

        class FixedDate(date):
            @classmethod
            def today(cls):
                return cls(2026, 7, 25)

        with patch('sis.views.date', FixedDate):
            calendar_data = _build_dashboard_calendar_data(request, date(2026, 7, 1))

        today_marked = [
            day for week in calendar_data['calendar_weeks'] for day in week if day.get('is_today')
        ]

        self.assertEqual(len(today_marked), 1)
        self.assertEqual(today_marked[0]['day'], 25)

    def test_e_path_redirects_to_students(self):
        response = self.client.get("/e")
        self.assertRedirects(response, reverse("dashboard"))

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

    def test_staff_registration_uploads_profile_picture(self):
        classroom = ClassRoom.objects.create(class_name="JHS 2")
        subject = Subject.objects.create(subject_name="Science")
        image_bytes = io.BytesIO()
        Image.new("RGB", (100, 100), color="blue").save(image_bytes, format="PNG")
        uploaded_file = SimpleUploadedFile(
            "avatar.png",
            image_bytes.getvalue(),
            content_type="image/png",
        )

        response = self.client.post(reverse("register_staff"), {
            "title": "Ms.",
            "first_name": "Ama",
            "last_name": "Boateng",
            "staff_id": "STAFF-002",
            "gender": "Female",
            "dob": "1990-02-02",
            "designation": "Teacher",
            "email": "ama@example.com",
            "employment_type": "Permanent",
            "date_of_appointment": "2021-01-01",
            "department": "Science",
            "qualification": "Degree",
            "certificate": "B.Ed",
            "name_of_institution_completed": "KNUST",
            "year_completed": "2021",
            "form_class": classroom.id,
            "subject_areas": [subject.id],
            "profile_picture": uploaded_file,
        })

        self.assertEqual(response.status_code, 302)
        staff = StaffProfile.objects.get(staff_id="STAFF-002")
        self.assertTrue(staff.profile_picture)

    def test_staff_avatar_initial_uses_name_when_no_picture(self):
        staff = StaffProfile.objects.create(
            first_name="Ada",
            last_name="Lovelace",
            staff_id="STAFF-003",
            email="ada@example.com",
        )

        self.assertEqual(staff.avatar_initial, "A")

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
        session = AcademicSession.objects.create(academic_year="2025/2026", is_current=True)
        term = Term.objects.create(session=session, term_name="Term 1", is_active=True)
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
        ClassSubject.objects.create(classroom=classroom, subject=subject)
        SubjectAssessment.objects.create(
            student=student,
            subject=subject,
            academic_session=session,
            academic_term=term,
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
        session = AcademicSession.objects.create(academic_year="2025/2026", is_current=True)
        term = Term.objects.create(session=session, term_name="Term 1", is_active=True)
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
        self.assertContains(response, "No student grade records compiled for this class yet")

    def test_class_report_empty_state_shows_master_records_pill(self):
        classroom = ClassRoom.objects.create(class_name="Class Empty Pill")
        url = reverse("class_report", kwargs={"class_id": classroom.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["has_graded_records"])
        self.assertContains(response, "View Master Records")

    def test_admin_report_landing_shows_staff_empty_state_with_pill(self):
        from django.contrib.auth.models import User

        self.client.logout()
        User.objects.create_superuser(username="repadmin", password="password")
        self.client.login(username="repadmin", password="password")
        classroom = ClassRoom.objects.create(class_name="Class Admin Empty")
        url = reverse("class_report", kwargs={"class_id": classroom.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["has_graded_records"])
        self.assertTrue(response.context["has_class_subject_assignment"])
        self.assertTrue(response.context["is_admin_landing"])
        self.assertContains(response, "Group%208381.svg")
        self.assertContains(response, "View Master Records")
        self.assertContains(response, "No student grade records compiled for this class yet")

    def test_admin_report_landing_with_data_still_shows_empty_design_then_master(self):
        from django.contrib.auth.models import User

        self.client.logout()
        User.objects.create_superuser(username="repadmin2", password="password")
        self.client.login(username="repadmin2", password="password")
        classroom = ClassRoom.objects.create(class_name="Class Admin Data")
        session = AcademicSession.objects.create(academic_year="2025/2026", is_current=True)
        term = Term.objects.create(session=session, term_name="Term 1", is_active=True)
        student = Student.objects.create(
            admission_number="ADM-1",
            first_name="Data",
            last_name="Kid",
            gender="Female",
            dob="2011-01-01",
            status="Day",
            current_class=classroom,
        )
        subject = Subject.objects.create(subject_name="Maths")
        ClassSubject.objects.create(classroom=classroom, subject=subject)
        SubjectAssessment.objects.create(
            student=student, subject=subject,
            academic_session=session, academic_term=term,
            class_score=20, exam_score=40,
        )
        url = reverse("class_report", kwargs={"class_id": classroom.id})

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["has_graded_records"])
        self.assertTrue(response.context["is_admin_landing"])
        self.assertContains(response, "View Master Records")

        master = self.client.get(url + "?master=1")
        self.assertEqual(master.status_code, 200)
        self.assertFalse(master.context["is_admin_landing"])
        self.assertTrue(master.context["is_master"])
        self.assertContains(master, "Data Kid")

    def test_class_report_with_grades_displays_table(self):
        classroom = ClassRoom.objects.create(class_name="Class Graded")
        session = AcademicSession.objects.create(academic_year="2025/2026", is_current=True)
        term = Term.objects.create(session=session, term_name="Term 1", is_active=True)
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
        ClassSubject.objects.create(classroom=classroom, subject=subject)
        SubjectAssessment.objects.create(
            student=student,
            subject=subject,
            academic_session=session,
            academic_term=term,
            class_score=30,
            exam_score=50,
        )
        url = reverse("class_report", kwargs={"class_id": classroom.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["has_graded_records"])
        self.assertTrue(response.context["is_admin_landing"])
        self.assertContains(response, "No student grade records compiled for this class yet")

        master = self.client.get(url + "?master=1")
        self.assertEqual(master.status_code, 200)
        self.assertTrue(master.context["has_graded_records"])
        self.assertFalse(master.context["is_admin_landing"])
        self.assertContains(master, "Evelyn Standings")


class FormMasterStudentVisibilityTests(TestCase):
    def setUp(self):
        from django.contrib.auth.models import User

        self.classroom = ClassRoom.objects.create(class_name="JHS 1")
        self.student = Student.objects.create(
            admission_number="FM-001",
            first_name="Kofi",
            last_name="Mensah",
            gender="Male",
            dob="2011-01-01",
            status="Day",
            classroom=self.classroom,
        )
        user = User.objects.create_user(username="formmaster", password="password")
        StaffProfile.objects.create(
            staff_id="FM-TEACHER-001",
            first_name="Form",
            last_name="Master",
            email="formmaster@example.com",
            user=user,
            form_class=self.classroom,
        )
        self.client.login(username="formmaster", password="password")

    def test_form_master_sees_students_of_form_class_in_directory(self):
        response = self.client.get(reverse("student_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Kofi  Mensah")

    def test_form_master_without_teaching_assignment_still_sees_form_class(self):
        other_class = ClassRoom.objects.create(class_name="JHS 2")
        other_student = Student.objects.create(
            admission_number="FM-002",
            first_name="Ama",
            last_name="Serwaa",
            gender="Female",
            dob="2011-02-02",
            status="Day",
            classroom=other_class,
        )
        response = self.client.get(reverse("student_list"))
        self.assertContains(response, "Kofi  Mensah")
        self.assertNotContains(response, "Ama  Serwaa")


class ExportStaffExcelTests(TestCase):
    def setUp(self):
        import io

        from django.contrib.auth.models import User

        self._io = io
        self.user = User.objects.create_superuser(username="staffexport", password="password")
        self.client.login(username="staffexport", password="password")

    def test_export_staff_excel_includes_staff_rows(self):
        from django.contrib.auth.models import User

        dept = Department.objects.create(name="Sciences")
        des = Designation.objects.create(name="Head of Maths")
        cls = ClassRoom.objects.create(class_name="JHS 2", order=2)
        subject = Subject.objects.create(subject_name="Physics")
        s_user = User.objects.create_user(username="t1", email="t1@example.com", password="x")
        staff = StaffProfile.objects.create(
            staff_id="STF-100",
            title="Mr.",
            first_name="Kwesi",
            other_names="Kofi",
            last_name="Antwi",
            gender="Male",
            email="kwesi@example.com",
            phone_number="0244001234",
            department=dept,
            designation=des,
            form_class=cls,
            user=s_user,
        )
        staff.subject_areas.add(subject)

        response = self.client.get(reverse("export_staff_excel"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response["Content-Type"],
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        self.assertIn("Staff_Directory", response["Content-Disposition"])

        from openpyxl import load_workbook

        ws = load_workbook(self._io.BytesIO(response.content)).active
        header_row = [c.value for c in ws[3]]
        self.assertIn("Staff ID", header_row)
        self.assertIn("Designation", header_row)
        self.assertIn("Department", header_row)
        self.assertIn("Form Class", header_row)
        self.assertIn("Subject Areas", header_row)

        cell_values = [c.value for row in ws.iter_rows(min_row=4) for c in row if c.value is not None]
        self.assertIn("STF-100", cell_values)
        self.assertIn("Kwesi", cell_values)
        self.assertIn("Antwi", cell_values)
        self.assertIn("Sciences", cell_values)
        self.assertIn("Physics", cell_values)

    def test_export_staff_fab_only_for_superuser(self):
        response = self.client.get(reverse("staff_list"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["can_export"])
        self.assertContains(response, "Export to Excel")

        self.client.logout()
        from django.contrib.auth.models import User

        User.objects.create_user(username="plainstaff", password="password")
        self.client.login(username="plainstaff", password="password")
        response = self.client.get(reverse("staff_list"))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["can_export"])
        self.assertNotContains(response, "Export to Excel")

    def test_export_staff_excel_requires_superuser(self):
        self.client.logout()
        from django.contrib.auth.models import User

        User.objects.create_user(username="plainstaff2", password="password")
        self.client.login(username="plainstaff2", password="password")
        response = self.client.get(reverse("export_staff_excel"))
        self.assertEqual(response.status_code, 403)


class ExportExcelTests(TestCase):
    def setUp(self):
        import io

        from django.contrib.auth.models import User

        self._io = io
        self.user = User.objects.create_superuser(username="exportadmin", password="password")
        self.client.login(username="exportadmin", password="password")

    def test_export_students_excel_includes_linked_parents(self):
        classroom = ClassRoom.objects.create(class_name="JHS 1")
        father = Parent.objects.create(name="Kwame Mensah", telephone_number="0244000001")
        mother = Parent.objects.create(name="Ama Mensah", email="ama@example.com")
        Student.objects.create(
            admission_number="EX-001",
            first_name="Kofi",
            last_name="Mensah",
            gender="Male",
            dob="2011-01-01",
            status="Day",
            classroom=classroom,
            father=father,
            mother=mother,
        )

        response = self.client.get(reverse("export_students_excel"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response["Content-Type"],
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        self.assertIn("Students_Directory", response["Content-Disposition"])

        from openpyxl import load_workbook

        ws = load_workbook(self._io.BytesIO(response.content)).active
        header_row = [c.value for c in ws[3]]
        self.assertIn("Father Name", header_row)
        self.assertIn("Mother Phone", header_row)

        cell_values = [c.value for row in ws.iter_rows(min_row=4) for c in row if c.value is not None]
        self.assertIn("EX-001", cell_values)
        self.assertIn("Kwame Mensah", cell_values)
        self.assertIn("ama@example.com", cell_values)

    def test_export_parents_excel_includes_linked_students(self):
        classroom = ClassRoom.objects.create(class_name="JHS 1")
        parent = Parent.objects.create(name="Kwame Mensah", telephone_number="0244000001")
        Student.objects.create(
            admission_number="EX-002",
            first_name="Kofi",
            last_name="Mensah",
            gender="Male",
            dob="2011-01-01",
            status="Day",
            classroom=classroom,
            father=parent,
        )

        response = self.client.get(reverse("export_parents_excel"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("Parents_Directory", response["Content-Disposition"])

        from openpyxl import load_workbook

        ws = load_workbook(self._io.BytesIO(response.content)).active
        header_row = [c.value for c in ws[3]]
        self.assertIn("Parent Name", header_row)
        self.assertIn("Children (Name - Class)", header_row)

        cell_values = [c.value for row in ws.iter_rows(min_row=4) for c in row if c.value is not None]
        self.assertIn("Kwame Mensah", cell_values)
        self.assertIn("Kofi Mensah - JHS 1", cell_values)
