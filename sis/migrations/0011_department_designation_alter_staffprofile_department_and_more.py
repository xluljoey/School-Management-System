import django.db.models.deletion
from django.db import migrations, models


def populate_fk_tables(apps, schema_editor):
    StaffProfile = apps.get_model('sis', 'StaffProfile')
    Department = apps.get_model('sis', 'Department')
    Designation = apps.get_model('sis', 'Designation')

    dept_map = {}
    for staff in StaffProfile.objects.all():
        if staff.department and staff.department not in dept_map:
            dept_obj, _ = Department.objects.get_or_create(name=staff.department)
            dept_map[staff.department] = dept_obj.id

    desig_map = {}
    for staff in StaffProfile.objects.all():
        if staff.designation and staff.designation not in desig_map:
            desig_obj, _ = Designation.objects.get_or_create(name=staff.designation)
            desig_map[staff.designation] = desig_obj.id

    default_departments = [
        "Language Arts",
        "Science and Mathematics",
        "Humanities and Social Sciences",
        "Arts & Performance",
        "Administration",
    ]
    for name in default_departments:
        Department.objects.get_or_create(name=name)

    default_designations = [
        "Teacher",
        "Senior Superintendent",
        "Principal Superintendent",
        "Headteacher",
        "IT Support Officer",
    ]
    for name in default_designations:
        Designation.objects.get_or_create(name=name)


def copy_fk_data(apps, schema_editor):
    StaffProfile = apps.get_model('sis', 'StaffProfile')
    Department = apps.get_model('sis', 'Department')
    Designation = apps.get_model('sis', 'Designation')

    for staff in StaffProfile.objects.all():
        if staff.department:
            dept_obj, _ = Department.objects.get_or_create(name=staff.department)
            staff.department_new = dept_obj.id
        if staff.designation:
            desig_obj, _ = Designation.objects.get_or_create(name=staff.designation)
            staff.designation_new = desig_obj.id
        staff.save(update_fields=['department_new', 'designation_new'])


class Migration(migrations.Migration):

    dependencies = [
        ('sis', '0010_staffprofile_profile_picture_student_profile_picture'),
    ]

    operations = [
        migrations.CreateModel(
            name='Department',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Designation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
            ],
        ),
        migrations.RunPython(populate_fk_tables),
        migrations.AddField(
            model_name='staffprofile',
            name='department_new',
            field=models.IntegerField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='staffprofile',
            name='designation_new',
            field=models.IntegerField(null=True, blank=True),
        ),
        migrations.RunPython(copy_fk_data),
        migrations.RemoveField(
            model_name='staffprofile',
            name='department',
        ),
        migrations.RemoveField(
            model_name='staffprofile',
            name='designation',
        ),
        migrations.RenameField(
            model_name='staffprofile',
            old_name='department_new',
            new_name='department',
        ),
        migrations.RenameField(
            model_name='staffprofile',
            old_name='designation_new',
            new_name='designation',
        ),
        migrations.AlterField(
            model_name='staffprofile',
            name='department',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='sis.department'),
        ),
        migrations.AlterField(
            model_name='staffprofile',
            name='designation',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='sis.designation'),
        ),
    ]
