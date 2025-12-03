from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from attendance.models import UserProfile


class Command(BaseCommand):
    help = 'تنظیم نقش مدیر برای کاربر Admin'

    def handle(self, *args, **options):
        try:
            admin_user = User.objects.get(username='Admin')
            profile, created = UserProfile.objects.get_or_create(
                user=admin_user,
                defaults={'role': 'admin'}
            )
            if not created:
                profile.role = 'admin'
                profile.save()
            
            self.stdout.write(
                self.style.SUCCESS(f'نقش مدیر برای کاربر {admin_user.username} تنظیم شد.')
            )
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('کاربر Admin یافت نشد. لطفاً ابتدا superuser ایجاد کنید.')
            )

