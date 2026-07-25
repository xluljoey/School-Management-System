from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('sis', '0034_backfill_fk_fields'),
    ]

    operations = [
        # Make Enrollment FKs NOT NULL
        migrations.AlterField(
            model_name='enrollment',
            name='academic_session',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='sis.academicsession'),
        ),
        migrations.AlterField(
            model_name='enrollment',
            name='academic_term',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='sis.term'),
        ),
        # Remove Enrollment legacy fields
        migrations.RemoveField(
            model_name='enrollment',
            name='term',
        ),
        migrations.RemoveField(
            model_name='enrollment',
            name='academic_year',
        ),
        # Make SubjectAssessment FKs NOT NULL
        migrations.AlterField(
            model_name='subjectassessment',
            name='academic_session',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='sis.academicsession'),
        ),
        migrations.AlterField(
            model_name='subjectassessment',
            name='academic_term',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='sis.term'),
        ),
        # Remove SubjectAssessment legacy fields
        migrations.RemoveField(
            model_name='subjectassessment',
            name='term',
        ),
        migrations.RemoveField(
            model_name='subjectassessment',
            name='academic_year',
        ),
        # Make GradeVerification FKs NOT NULL
        migrations.AlterField(
            model_name='gradeverification',
            name='academic_session',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='sis.academicsession'),
        ),
        migrations.AlterField(
            model_name='gradeverification',
            name='academic_term',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='sis.term'),
        ),
        # Remove GradeVerification legacy fields
        migrations.RemoveField(
            model_name='gradeverification',
            name='term',
        ),
        migrations.RemoveField(
            model_name='gradeverification',
            name='academic_year',
        ),
    ]
