from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from attendance.models import UserProfile, Teacher


class Command(BaseCommand):
    help = 'اتصال کاربران معلم به معلمان (برای رفع مشکل کاربران بدون معلم)'

    def handle(self, *args, **options):
        self.stdout.write('=' * 60)
        self.stdout.write('بررسی و رفع مشکل کاربران معلم:')
        self.stdout.write('=' * 60)
        
        # پیدا کردن همه کاربران معلم
        teacher_profiles = UserProfile.objects.filter(role='teacher').select_related('teacher', 'user')
        
        self.stdout.write(f'\nتعداد کل کاربران معلم: {teacher_profiles.count()}')
        
        # کاربران بدون معلم
        users_without_teacher = [p for p in teacher_profiles if not p.teacher]
        self.stdout.write(f'کاربران معلم بدون معلم: {len(users_without_teacher)}')
        
        if users_without_teacher:
            self.stdout.write('\nدر حال ایجاد معلم برای کاربران بدون معلم...')
            for profile in users_without_teacher:
                user = profile.user
                self.stdout.write(f'\n  کاربر: {user.username} ({user.get_full_name() or user.username})')
                
                # استفاده از نام و نام خانوادگی کاربر
                first_name = user.first_name.strip() if user.first_name else user.username
                last_name = user.last_name.strip() if user.last_name else ''
                
                if not last_name:
                    username_parts = user.username.replace('_', ' ').split()
                    if len(username_parts) > 1:
                        first_name = username_parts[0]
                        last_name = ' '.join(username_parts[1:])
                    else:
                        first_name = user.username
                        last_name = ''
                
                phone_number = profile.phone_number if profile.phone_number else None
                
                # بررسی وجود معلم با همین نام
                teacher = Teacher.objects.filter(
                    first_name=first_name,
                    last_name=last_name
                ).first()
                
                if not teacher:
                    teacher = Teacher.objects.create(
                        first_name=first_name,
                        last_name=last_name,
                        phone_number=phone_number
                    )
                    self.stdout.write(
                        self.style.SUCCESS(f'  ✓ معلم جدید ایجاد شد: {teacher.first_name} {teacher.last_name}')
                    )
                else:
                    self.stdout.write(f'  ✓ معلم موجود یافت شد: {teacher.first_name} {teacher.last_name}')
                    if not teacher.phone_number and phone_number:
                        teacher.phone_number = phone_number
                        teacher.save(update_fields=['phone_number'])
                        self.stdout.write(self.style.SUCCESS('  ✓ شماره تلفن معلم به‌روزرسانی شد'))
                
                # اتصال معلم به پروفایل
                profile.teacher = teacher
                profile.save(update_fields=['teacher'])
                self.stdout.write(self.style.SUCCESS('  ✓ معلم به کاربر متصل شد'))
        else:
            self.stdout.write(self.style.SUCCESS('\n✅ همه کاربران معلم به معلمان متصل هستند!'))
        
        # بررسی نهایی
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write('نتیجه نهایی:')
        self.stdout.write('=' * 60)
        final_check = UserProfile.objects.filter(role='teacher', teacher__isnull=True).count()
        self.stdout.write(f'کاربران معلم بدون معلم: {final_check}')
        if final_check == 0:
            self.stdout.write(self.style.SUCCESS('✅ همه کاربران معلم به معلمان متصل هستند!'))
        else:
            self.stdout.write(self.style.ERROR(f'❌ هنوز {final_check} کاربر معلم بدون معلم وجود دارد!'))

