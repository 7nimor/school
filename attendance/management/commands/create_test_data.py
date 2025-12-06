from django.core.management.base import BaseCommand
from attendance.models import Teacher, Class, Parent, Student, Attendance
from datetime import date, timedelta
import random


class Command(BaseCommand):
    help = 'ایجاد داده‌های تستی برای سیستم حضور و غیاب'

    def handle(self, *args, **options):
        self.stdout.write('در حال ایجاد داده‌های تستی...')
        
        # ایجاد معلمان
        teachers_data = [
            {'first_name': 'علی', 'last_name': 'احمدی', 'phone_number': '09123456789'},
            {'first_name': 'مریم', 'last_name': 'رضایی', 'phone_number': '09123456790'},
            {'first_name': 'حسین', 'last_name': 'کریمی', 'phone_number': '09123456791'},
            {'first_name': 'فاطمه', 'last_name': 'محمدی', 'phone_number': '09123456792'},
        ]
        
        teachers = []
        for teacher_data in teachers_data:
            teacher, created = Teacher.objects.get_or_create(
                phone_number=teacher_data['phone_number'],
                defaults=teacher_data
            )
            teachers.append(teacher)
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ معلم ایجاد شد: {teacher}'))
        
        # ایجاد کلاس‌ها
        classes_data = [
            {'name': 'الف', 'grade': 'اول', 'teacher': teachers[0]},
            {'name': 'ب', 'grade': 'اول', 'teacher': teachers[1]},
            {'name': 'الف', 'grade': 'دوم', 'teacher': teachers[2]},
            {'name': 'ب', 'grade': 'دوم', 'teacher': teachers[3]},
            {'name': 'الف', 'grade': 'سوم', 'teacher': teachers[0]},
        ]
        
        classes = []
        for class_data in classes_data:
            class_obj, created = Class.objects.get_or_create(
                name=class_data['name'],
                grade=class_data['grade'],
                defaults=class_data
            )
            classes.append(class_obj)
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ کلاس ایجاد شد: {class_obj}'))
        
        # ایجاد اولیا
        parents_data = [
            {'first_name': 'محمد', 'last_name': 'حسینی', 'phone_number': '09121111111'},
            {'first_name': 'زهرا', 'last_name': 'علیزاده', 'phone_number': '09121111112'},
            {'first_name': 'رضا', 'last_name': 'نوری', 'phone_number': '09121111113'},
            {'first_name': 'سارا', 'last_name': 'موسوی', 'phone_number': '09121111114'},
            {'first_name': 'امیر', 'last_name': 'جعفری', 'phone_number': '09121111115'},
            {'first_name': 'نرگس', 'last_name': 'صادقی', 'phone_number': '09121111116'},
            {'first_name': 'حامد', 'last_name': 'کاظمی', 'phone_number': '09121111117'},
            {'first_name': 'لیلا', 'last_name': 'باقری', 'phone_number': '09121111118'},
            {'first_name': 'مهدی', 'last_name': 'فرهادی', 'phone_number': '09121111119'},
            {'first_name': 'مینا', 'last_name': 'شریفی', 'phone_number': '09121111120'},
            {'first_name': 'پویا', 'last_name': 'اکبری', 'phone_number': '09121111121'},
            {'first_name': 'نیلوفر', 'last_name': 'قاسمی', 'phone_number': '09121111122'},
            {'first_name': 'سینا', 'last_name': 'رحیمی', 'phone_number': '09121111123'},
            {'first_name': 'آتوسا', 'last_name': 'طاهری', 'phone_number': '09121111124'},
            {'first_name': 'کیوان', 'last_name': 'مرادی', 'phone_number': '09121111125'},
        ]
        
        parents = []
        for parent_data in parents_data:
            parent, created = Parent.objects.get_or_create(
                phone_number=parent_data['phone_number'],
                defaults=parent_data
            )
            parents.append(parent)
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ اولیا ایجاد شد: {parent}'))
        
        # ایجاد دانش‌آموزان
        students_data = [
            {'first_name': 'امیرعلی', 'last_name': 'حسینی', 'student_id': '1401-001', 'parent': parents[0], 'class_room': classes[0]},
            {'first_name': 'فاطمه', 'last_name': 'علیزاده', 'student_id': '1401-002', 'parent': parents[1], 'class_room': classes[0]},
            {'first_name': 'علی', 'last_name': 'نوری', 'student_id': '1401-003', 'parent': parents[2], 'class_room': classes[0]},
            {'first_name': 'زهرا', 'last_name': 'موسوی', 'student_id': '1401-004', 'parent': parents[3], 'class_room': classes[1]},
            {'first_name': 'محمد', 'last_name': 'جعفری', 'student_id': '1401-005', 'parent': parents[4], 'class_room': classes[1]},
            {'first_name': 'سارا', 'last_name': 'صادقی', 'student_id': '1402-001', 'parent': parents[5], 'class_room': classes[2]},
            {'first_name': 'حسین', 'last_name': 'کاظمی', 'student_id': '1402-002', 'parent': parents[6], 'class_room': classes[2]},
            {'first_name': 'مریم', 'last_name': 'باقری', 'student_id': '1402-003', 'parent': parents[7], 'class_room': classes[3]},
            {'first_name': 'رضا', 'last_name': 'فرهادی', 'student_id': '1402-004', 'parent': parents[8], 'class_room': classes[3]},
            {'first_name': 'نرگس', 'last_name': 'شریفی', 'student_id': '1403-001', 'parent': parents[9], 'class_room': classes[4]},
            {'first_name': 'پویا', 'last_name': 'اکبری', 'student_id': '1403-002', 'parent': parents[10], 'class_room': classes[4]},
            {'first_name': 'نیلوفر', 'last_name': 'قاسمی', 'student_id': '1403-003', 'parent': parents[11], 'class_room': classes[4]},
            {'first_name': 'سینا', 'last_name': 'رحیمی', 'student_id': '1401-006', 'parent': parents[12], 'class_room': classes[0]},
            {'first_name': 'آتوسا', 'last_name': 'طاهری', 'student_id': '1401-007', 'parent': parents[13], 'class_room': classes[1]},
            {'first_name': 'کیوان', 'last_name': 'مرادی', 'student_id': '1402-005', 'parent': parents[14], 'class_room': classes[2]},
        ]
        
        students = []
        for student_data in students_data:
            # حذف student_id از داده‌ها
            student_data_clean = {k: v for k, v in student_data.items() if k != 'student_id'}
            student, created = Student.objects.get_or_create(
                first_name=student_data_clean['first_name'],
                last_name=student_data_clean['last_name'],
                class_room=student_data_clean['class_room'],
                defaults=student_data_clean
            )
            students.append(student)
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ دانش‌آموز ایجاد شد: {student}'))
        
        # ایجاد رکوردهای حضور و غیاب برای 7 روز گذشته
        statuses = [Attendance.PRESENT, Attendance.PRESENT, Attendance.PRESENT, 
                   Attendance.ABSENT, Attendance.LATE, Attendance.EXCUSED]
        
        today = date.today()
        attendance_count = 0
        
        for day_offset in range(7):
            attendance_date = today - timedelta(days=day_offset)
            
            for student in students:
                # 80% احتمال حضور
                if random.random() < 0.8:
                    status = random.choice([Attendance.PRESENT, Attendance.PRESENT, Attendance.PRESENT, Attendance.LATE])
                else:
                    status = random.choice([Attendance.ABSENT, Attendance.EXCUSED])
                
                attendance, created = Attendance.objects.get_or_create(
                    student=student,
                    date=attendance_date,
                    defaults={
                        'status': status,
                        'sms_sent': status == Attendance.ABSENT and random.random() < 0.5,  # 50% احتمال ارسال پیامک
                    }
                )
                
                if created:
                    attendance_count += 1
        
        self.stdout.write(self.style.SUCCESS(f'\n✓ {attendance_count} رکورد حضور و غیاب ایجاد شد'))
        self.stdout.write(self.style.SUCCESS('\n✅ داده‌های تستی با موفقیت ایجاد شدند!'))
        self.stdout.write(f'\n📊 خلاصه:')
        self.stdout.write(f'   - معلمان: {len(teachers)}')
        self.stdout.write(f'   - کلاس‌ها: {len(classes)}')
        self.stdout.write(f'   - اولیا: {len(parents)}')
        self.stdout.write(f'   - دانش‌آموزان: {len(students)}')
        self.stdout.write(f'   - حضور و غیاب: {attendance_count}')

