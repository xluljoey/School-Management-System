from django.db import migrations


def forward(apps, schema_editor):
    AcademicSession = apps.get_model('sis', 'AcademicSession')
    Term = apps.get_model('sis', 'Term')
    SubjectAssessment = apps.get_model('sis', 'SubjectAssessment')
    Enrollment = apps.get_model('sis', 'Enrollment')

    session_map = {}
    for session in AcademicSession.objects.all():
        session_map[session.academic_year] = session

    term_map = {}
    for term in Term.objects.select_related('session').all():
        term_map[(term.session_id, term.term_name)] = term

    term_number_to_name = {1: 'Term 1', 2: 'Term 2', 3: 'Term 3'}

    updated_assessments = 0
    for sa in SubjectAssessment.objects.filter(academic_session__isnull=True):
        session = session_map.get(sa.academic_year)
        if not session:
            continue
        term_name = term_number_to_name.get(sa.term)
        if not term_name:
            continue
        term = term_map.get((session.id, term_name))
        if not term:
            continue
        sa.academic_session = session
        sa.academic_term = term
        sa.save(update_fields=['academic_session', 'academic_term'])
        updated_assessments += 1

    updated_enrollments = 0
    for en in Enrollment.objects.filter(academic_session__isnull=True):
        session = session_map.get(en.academic_year)
        if not session:
            continue
        term = term_map.get((session.id, en.term))
        if not term:
            continue
        en.academic_session = session
        en.academic_term = term
        en.save(update_fields=['academic_session', 'academic_term'])
        updated_enrollments += 1

    print(f"  Backfilled {updated_assessments} SubjectAssessment records")
    print(f"  Backfilled {updated_enrollments} Enrollment records")


def reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('sis', '0033_alter_enrollment_unique_together_and_more'),
    ]

    operations = [
        migrations.RunPython(forward, reverse),
    ]
