# Generated manually
from django.db import migrations, models
import django.db.models.deletion
import django.core.validators


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Parent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first_name', models.CharField(max_length=100, verbose_name='نام')),
                ('last_name', models.CharField(max_length=100, verbose_name='نام خانوادگی')),
                ('phone_number', models.CharField(max_length=11, unique=True, validators=[django.core.validators.RegexValidator(message='شماره تلفن باید با فرمت 09123456789 باشد', regex='^09\\d{9}$')], verbose_name='شماره تلفن')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')),
            ],
            options={
                'verbose_name': 'والد',
                'verbose_name_plural': 'والدین',
                'ordering': ['last_name', 'first_name'],
            },
        ),
        migrations.CreateModel(
            name='Student',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first_name', models.CharField(max_length=100, verbose_name='نام')),
                ('last_name', models.CharField(max_length=100, verbose_name='نام خانوادگی')),
                ('student_id', models.CharField(max_length=20, unique=True, verbose_name='شماره دانش\u200cآموزی')),
                ('is_active', models.BooleanField(default=True, verbose_name='فعال')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')),
                ('parent', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='students', to='attendance.parent', verbose_name='والد/سرپرست')),
            ],
            options={
                'verbose_name': 'دانش\u200cآموز',
                'verbose_name_plural': 'دانش\u200cآموزان',
                'ordering': ['last_name', 'first_name'],
            },
        ),
        migrations.CreateModel(
            name='Attendance',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(verbose_name='تاریخ')),
                ('status', models.CharField(choices=[('present', 'حاضر'), ('absent', 'غایب'), ('excused', 'غایب موجه'), ('late', 'تأخیر')], default='present', max_length=10, verbose_name='وضعیت')),
                ('notes', models.TextField(blank=True, null=True, verbose_name='یادداشت')),
                ('sms_sent', models.BooleanField(default=False, verbose_name='پیامک ارسال شده')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='تاریخ بروزرسانی')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attendances', to='attendance.student', verbose_name='دانش\u200cآموز')),
            ],
            options={
                'verbose_name': 'حضور و غیاب',
                'verbose_name_plural': 'حضور و غیاب\u200cها',
                'ordering': ['-date', 'student'],
            },
        ),
        migrations.AddConstraint(
            model_name='attendance',
            constraint=models.UniqueConstraint(fields=('student', 'date'), name='attendance_attendance_student_date_uniq'),
        ),
    ]

