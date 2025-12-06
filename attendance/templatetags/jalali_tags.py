from django import template
import jdatetime

register = template.Library()


@register.filter
def jalali_date(value):
    """تبدیل تاریخ میلادی به شمسی"""
    if value:
        try:
            if hasattr(value, 'year') and hasattr(value, 'month') and hasattr(value, 'day'):
                # date object
                jalali = jdatetime.date.fromgregorian(date=value)
                return jalali.strftime('%Y/%m/%d')
            else:
                return str(value)
        except Exception as e:
            return str(value)
    return value


@register.filter
def jalali_datetime(value):
    """تبدیل تاریخ و زمان میلادی به شمسی"""
    if value:
        try:
            if hasattr(value, 'date'):
                jalali = jdatetime.datetime.fromgregorian(datetime=value)
            else:
                jalali = jdatetime.datetime.fromgregorian(date=value)
            return jalali.strftime('%Y/%m/%d %H:%M')
        except:
            return value
    return value


@register.filter
def jalali_date_full(value):
    """تبدیل تاریخ میلادی به شمسی با نام ماه"""
    if value:
        try:
            if hasattr(value, 'year') and hasattr(value, 'month') and hasattr(value, 'day'):
                # date object
                jalali = jdatetime.date.fromgregorian(date=value)
                months = ['فروردین', 'اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور',
                         'مهر', 'آبان', 'آذر', 'دی', 'بهمن', 'اسفند']
                return f"{jalali.day} {months[jalali.month - 1]} {jalali.year}"
            else:
                return str(value)
        except Exception as e:
            return str(value)
    return value


@register.filter
def default_dash(value):
    """تبدیل None، null، و رشته خالی به '-'"""
    if value is None or value == '' or str(value).lower() in ['none', 'null']:
        return '-'
    return value

