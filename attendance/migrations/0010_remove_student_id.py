# Generated manually

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('attendance', '0009_remove_unique_parent_phone'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='student',
            name='student_id',
        ),
    ]

