# School Management System - Database Schema (LAN/Offline-First)
**Backend Framework:** Django  
**Database Engine:** PostgreSQL (or SQLite for development)

---

## 1. Core Users & System Tables

### Table: Auth_User (Built-in Django Model)
* Handles standard system access and permissions.
* Fields:
  * `id` (INT, PK, Auto-increment)
  * `username` (VARCHAR, Unique) -> *Used for Staff_ID or Admin Username*
  * `password` (VARCHAR) -> *Encrypted hash out-of-the-box*
  * `is_superuser` (BOOLEAN) -> *True for System Admins*
  * `is_staff` (BOOLEAN) -> *True for Teachers/Staff*

### Table: ClassRoom
* Defines the classes or forms in the school.
* Fields:
  * `class_id` (INT, PK, Auto-increment)
  * `class_name` (VARCHAR, Unique) -> *e.g., JHS 1A, Class 3B*

### Table: Subject
* Stores all the subjects taught in the school.
* Fields:
  * `subject_id` (INT, PK, Auto-increment)
  * `subject_name` (VARCHAR, Unique) -> *e.g., Mathematics, Integrated Science*

---

## 2. Profiles (People Data)

### Table: StaffProfile
* Extended details for teachers and administrative staff.
* Fields:
  * `staff_id` (VARCHAR, PK) -> *e.g., GES-ST-2026-001*
  * `user_id` (INT, FK) -> *Points to Auth_User (One-to-One Link)*
  * `title` (VARCHAR) -> *e.g., Mr., Mrs., Dr.*
  * `first_name` (VARCHAR)
  * `last_name` (VARCHAR)
  * `gender` (VARCHAR)
  * `dob` (DATE)
  * `designation` (VARCHAR) -> *e.g., Form Master, Subject Teacher*
  * `department` (VARCHAR)
  * `ssnit_id` (VARCHAR, Nullable)
  * `email` (VARCHAR, Nullable)
  * `employment_type` (VARCHAR) -> *e.g., Permanent, Temporary*
  * `date_of_appointment` (DATE)
  * `year_last_promotion` (INT)
  * `qualification` (VARCHAR)
  * `institution_completed` (VARCHAR)
  * `year_completed` (INT)
  * `form_class_id` (INT, FK, Nullable) -> *Points to ClassRoom (If they manage a specific class)*

> **Note on Subjects Taught:** Django manages this via a Many-to-Many junction table (`StaffProfile_Subjects`) automatically behind the scenes when you use `ManyToManyField(Subject)`.

### Table: Student
* Stores current and historical student records.
* Fields:
  * `student_id` (INT, PK, Auto-increment)
  * `admission_number` (VARCHAR, Unique) -> *Generated Index/Admission number*
  * `first_name` (VARCHAR)
  * `last_name` (VARCHAR)
  * `gender` (VARCHAR)
  * `dob` (DATE)
  * `status` (VARCHAR) -> *Day / Boarder*
  * `date_of_admission` (DATE)
  * `previous_school` (VARCHAR, Nullable)
  * `parents_living_with` (VARCHAR) -> *Mother / Father / Both / Guardian*
  * `current_class_id` (INT, FK) -> *Points to ClassRoom*

### Table: ParentGuardian
* Stores family contact information linked back to the student.
* Fields:
  * `parent_id` (INT, PK, Auto-increment)
  * `student_id` (INT, FK) -> *Points to Student (One student can have multiple parents/guardians entered)*
  * `relationship` (VARCHAR) -> *Mother / Father / Guardian*
  * `name` (VARCHAR)
  * `occupation` (VARCHAR)
  * `residential_address` (TEXT)
  * `email` (VARCHAR, Nullable)
  * `telephone` (VARCHAR)

---

## 3. The Assessment & Grading Engine

### Table: SubjectAssessment
* Captures raw terminal scores per subject for each student.
* Fields:
  * `assessment_id` (INT, PK, Auto-increment)
  * `student_id` (INT, FK) -> *Points to Student*
  * `subject_id` (INT, FK) -> *Points to Subject*
  * `term` (INT) -> *1, 2, or 3*
  * `academic_year` (VARCHAR) -> *e.g., 2025/2026*
  * `class_score` (DECIMAL) -> *SBA component, usually out of 30 or 40*
  * `exam_score` (DECIMAL) -> *Exam component, usually out of 70 or 60*

### Table: TermSummary
* Non-academic metadata required on final report sheets.
* Fields:
  * `summary_id` (INT, PK, Auto-increment)
  * `student_id` (INT, FK) -> *Points to Student*
  * `term` (INT)
  * `academic_year` (VARCHAR)
  * `attendance_present` (INT)
  * `attendance_total` (INT)
  * `teacher_remarks` (TEXT, Nullable)
  * `headteacher_remarks` (TEXT, Nullable)

---
### Architectural Design Rule Reminder
*Calculated data (`Total_Score`, `Position_in_Subject`, `Grand_Total`, `Position_in_Class`) is **never** hardcoded into the tables. Python code dynamically loops through the records at runtime to perform rankings and sums, protecting data integrity from updates or corrections.*
