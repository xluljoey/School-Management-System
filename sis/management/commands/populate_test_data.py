from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import transaction
from sis.models import (
    ClassRoom, Subject, Department, Designation, StaffProfile,
    Student, StaffClassSubject, AcademicSession, Term, Enrollment,
)
from datetime import date
import random


CLASS_ORDER_MAP = {
    'JHS 3': 30,
    'JHS 2': 20,
    'JHS 1': 10,
    'CLASS 1': 5,
}

STAFF_DATA = [
    {'first': 'Kwame', 'last': 'Mensah', 'gender': 'Male',   'title': 'Mr.'},
    {'first': 'Abena',  'last': 'Osei',   'gender': 'Female', 'title': 'Mrs.'},
    {'first': 'Kofi',   'last': 'Boateng','gender': 'Male',   'title': 'Mr.'},
    {'first': 'Akosua', 'last': 'Appiah', 'gender': 'Female', 'title': 'Ms.'},
    {'first': 'Yaw',    'last': 'Adjei',  'gender': 'Male',   'title': 'Mr.'},
    {'first': 'Efua',   'last': 'Sackey', 'gender': 'Female', 'title': 'Mrs.'},
    {'first': 'Nana',   'last': 'Amoako', 'gender': 'Male',   'title': 'Mr.'},
    {'first': 'Adwoa',  'last': 'Asante', 'gender': 'Female', 'title': 'Ms.'},
]

SUBJECT_DEPT = [
    ('Mathematics',        'Science & Mathematics'),
    ('English Language',   'Language Arts'),
    ('Integrated Science', 'Science & Mathematics'),
    ('Social Studies',     'Humanities'),
]

STUDENT_FIRST_NAMES = ['Yaw', 'Ekow', 'Ama', 'Afia', 'Kweku', 'Baaba', 'Kofi', 'Akosua', 'Adwoa', 'Kwame', 'Abena', 'Yaa']
STUDENT_LAST_NAMES  = ['Danso', 'Agyei', 'Koomson', 'Addo', 'Asare', 'Arthur', 'Boateng', 'Mensah', 'Osei', 'Sackey', 'Amoako', 'Asante']


class Command(BaseCommand):
    help = 'Populate the database with realistic test data (classes, staff, students).'

    def handle(self, *args, **options):
        self._purge_previous_test_data()
        self._ensure_academic_env()
        self._update_class_orders()
        dep_map = self._ensure_departments_and_subjects()
        self._provision_staff(dep_map)
        self._generate_students()
        self.stdout.write(self.style.SUCCESS('Done.'))

    def _purge_previous_test_data(self):
        Student.objects.filter(admission_number__startswith='ADM-2026-').delete()
        StaffClassSubject.objects.filter(staff__staff_id__startswith='STF-2026-').delete()
        StaffProfile.objects.filter(staff_id__startswith='STF-2026-').delete()
        User.objects.filter(
            username__in=[d['first'].lower() for d in STAFF_DATA]
        ).delete()
        # Clear form_class from any staff pointing to our classrooms
        StaffProfile.objects.filter(
            form_class__class_name__in=CLASS_ORDER_MAP
        ).update(form_class=None)
        self.stdout.write('  ✓ Purged previous test data')

    # ------------------------------------------------------------------
    # 1  –  Academic session / term
    # ------------------------------------------------------------------
    def _ensure_academic_env(self):
        session, _ = AcademicSession.objects.get_or_create(
            academic_year='2025/2026',
            defaults={'is_current': True},
        )
        Term.objects.get_or_create(
            session=session,
            term_name='Term 1',
            defaults={'is_active': True},
        )
        self.stdout.write('  ✓ Academic session 2025/2026 / Term 1')

    # ------------------------------------------------------------------
    # 2  –  Class hierarchy
    # ------------------------------------------------------------------
    def _update_class_orders(self):
        for class_name, order_val in CLASS_ORDER_MAP.items():
            cls, created = ClassRoom.objects.get_or_create(
                class_name=class_name,
                defaults={'order': order_val},
            )
            if not created and cls.order != order_val:
                cls.order = order_val
                cls.save()
        self.stdout.write(f'  ✓ {len(CLASS_ORDER_MAP)} classes ensured')

    # ------------------------------------------------------------------
    # 3  –  Departments & Subjects
    # ------------------------------------------------------------------
    def _ensure_departments_and_subjects(self):
        for subj_name, dept_name in SUBJECT_DEPT:
            Department.objects.get_or_create(name=dept_name)
            Subject.objects.get_or_create(subject_name=subj_name)
        self.stdout.write(f'  ✓ {len(SUBJECT_DEPT)} subjects / 3 departments')
        return {d.name: d for d in Department.objects.all()}

    # ------------------------------------------------------------------
    # 4  –  Staff profiles + user accounts
    # ------------------------------------------------------------------
    @transaction.atomic
    def _provision_staff(self, dep_map):
        classrooms = list(ClassRoom.objects.filter(
            class_name__in=CLASS_ORDER_MAP
        ).order_by('-order'))
        subjects = list(Subject.objects.all())

        desig, _ = Designation.objects.get_or_create(name='Teacher')
        dept_names = list(dep_map.keys())

        for idx, data in enumerate(STAFF_DATA):
            username = data['first'].lower()
            email = f"{username}.{data['last'].lower()}@school.edu"
            staff_id = f'STF-2026-{idx + 1:03d}'

            user = User.objects.create_user(
                username=username,
                password='TestPass123!',
                first_name=data['first'],
                last_name=data['last'],
                email=email,
            )

            profile = StaffProfile.objects.create(
                user=user,
                title=data['title'],
                first_name=data['first'],
                last_name=data['last'],
                staff_id=staff_id,
                gender=data['gender'],
                email=email,
                department=dep_map[dept_names[idx % len(dept_names)]],
                designation=desig,
                dob=date(1990, 1, 1),
                qualification='Degree',
                certificate='B.Ed',
                name_of_institution_completed='University of Ghana',
                year_completed=2015,
                form_class=classrooms[idx] if idx < len(classrooms) else None,
            )

            if idx < len(classrooms):
                self.stdout.write(
                    f'  ✓ {data["first"]} {data["last"]} → form teacher of {classrooms[idx].class_name}'
                )
            else:
                target_class = classrooms[idx % len(classrooms)]
                for subj in subjects:
                    StaffClassSubject.objects.create(
                        staff=profile,
                        classroom=target_class,
                        subject=subj,
                    )
                self.stdout.write(
                    f'  ✓ {data["first"]} {data["last"]} → subject teacher ({target_class.class_name})'
                )

        self.stdout.write(self.style.SUCCESS(f'  ✔ {len(STAFF_DATA)} staff created'))

    # ------------------------------------------------------------------
    # 5  –  ~120 students (30 per class)
    # ------------------------------------------------------------------
    @transaction.atomic
    def _generate_students(self):
        classrooms = list(ClassRoom.objects.filter(
            class_name__in=CLASS_ORDER_MAP
        ).order_by('-order'))

        session = AcademicSession.objects.filter(is_current=True).first()
        term = Term.objects.filter(is_active=True).first() if session else None
        term_name = term.term_name if term else 'Term 1'
        acad_year = session.academic_year if session else '2025/2026'

        students_created = 0

        for ci, classroom in enumerate(classrooms):
            for i in range(30):
                first = random.choice(STUDENT_FIRST_NAMES)
                last = random.choice(STUDENT_LAST_NAMES)
                gender = 'Male' if first in ('Yaw', 'Ekow', 'Kweku', 'Kofi', 'Kwame') else 'Female'
                adm_no = f'ADM-2026-{(ci * 30 + i + 1):04d}'

                student = Student.objects.create(
                    admission_number=adm_no,
                    first_name=first,
                    last_name=last,
                    gender=gender,
                    status=random.choice(['Day', 'Boarder']),
                    dob=date(2010 + random.randint(1, 8), random.randint(1, 12), random.randint(1, 28)),
                    date_of_admission=date(2026, 1, random.randint(5, 20)),
                    classroom=classroom,
                    previous_school_attended=random.choice([
                        "St. Mary's Basic", 'Methodist Basic', 'Presby Basic',
                        'Anglican Basic', 'Islamic Basic', 'Community School',
                    ]),
                )
                Enrollment.objects.create(
                    student=student,
                    classroom=classroom,
                    term=term_name,
                    academic_year=acad_year,
                )
                students_created += 1

            self.stdout.write(f'  ✓ {classroom.class_name} → 30 students seeded')

        self.stdout.write(self.style.SUCCESS(f'  ✔ {students_created} students created'))
