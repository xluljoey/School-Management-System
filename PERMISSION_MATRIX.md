# Permission Matrix — School Management System

## Overview

Score editing permissions are determined by **explicit `StaffClassSubject` assignment**, not by admin/superuser status. Admins retain read-only visibility across all classes and subjects.

---

## Role Permissions

| Role | View All Subjects | Edit Own Subjects | Edit All Subjects | Generate Reports |
|---|---|---|---|---|
| Admin (no `staff_profile`) | Yes | No | No | No |
| Admin (with `staff_profile` + assignment) | Yes | Yes (assigned only) | No | Yes (master view) |
| Admin (with `staff_profile`, no assignment) | Yes | No | No | Yes (master view) |
| Form Teacher | Yes | Yes | Yes (all in their class) | Yes (master view) |
| Subject Teacher | Yes | Yes (assigned only) | No (unless teaches all) | No |

---

## Key Models

| Model | Purpose |
|---|---|
| `StaffClassSubject` | Links a staff member to a specific classroom + subject. **Source of truth** for edit permissions. |
| `ClassSubject` | Declares which subjects are offered in a class. No teacher FK. |
| `StaffProfile` | Staff profile with `form_class` FK (one-to-one with ClassRoom). |

---

## Backend Permission Checks

### `class_report_card_view` (`views.py:416-427`)

```python
# can_modify_grades: True only if staff has StaffClassSubject assignment
can_modify_grades = False
if staff:
    if current_subject_id:
        can_modify_grades = StaffClassSubject.objects.filter(
            staff=staff, classroom=classroom, subject_id=current_subject_id
        ).exists()
    else:
        can_modify_grades = is_form_teacher or assigned_subjects.exists()

# can_edit_master: True if staff is assigned to ANY subject in the class
can_edit_master = bool(assigned_subject_ids_set)
```

### `api_edit_assessment` (`views.py:568-578`)

```python
# Requires staff_profile + StaffClassSubject match for the specific classroom+subject
staff = getattr(request.user, 'staff_profile', None)
if not staff:
    return JsonResponse({'error': ...}, status=403)
enrollment = student.enrollments.order_by('-date_enrolled').first()
is_assigned = StaffClassSubject.objects.filter(
    staff=staff, classroom=enrollment.classroom, subject=subject
).exists()
if not is_assigned:
    return JsonResponse({'error': ...}, status=403)
```

### `compile_grades_view` POST handler (`views.py:1534`)

```python
# Prevents unauthorized bulk grade saves
if not staff or not StaffClassSubject.objects.filter(
    staff=staff, classroom=classroom, subject=selected_subject
).exists():
    raise PermissionDenied
```

---

## Template Conditions (`class_report.html`)

| Element | Condition | Line |
|---|---|---|
| Master View toggle | `is_form_teacher or has_full_access` | 213 |
| "+ New Grade Entry" | `can_modify_grades` | 258 |
| Edit Scores FAB | `is_master and can_edit_master or not is_master and can_modify_grades` | 474 |
| Generate Report Cards | `is_master and is_form_teacher or is_master and has_full_access` | 490 |

`has_full_access` = `request.user.is_superuser or is_form_teacher` (used for view/generation, NOT edit).

---

## Design Principles

1. **Admin is not a teacher.** Superuser status grants read-only visibility and report generation, never score editing.
2. **Edit = explicit assignment.** Only `StaffClassSubject` records grant edit access.
3. **Form teacher = full edit in their class.** The form teacher can edit all subjects they teach (or all subjects in their class by virtue of form_class).
4. **Backend is the source of truth.** Template conditions hide UI; backend guards enforce security.
