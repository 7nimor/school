from django.apps import AppConfig


class AttendanceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'attendance'
    verbose_name = 'سیستم حضور و غیاب'
    
    def ready(self):
        import attendance.signals  # noqa

