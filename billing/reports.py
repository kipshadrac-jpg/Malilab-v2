"""Sales figures for the staff screen. Test-mode (sandbox) money is kept apart from live money."""
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from django.db.models import Count, Sum
from django.db.models.functions import TruncDate
from django.utils import timezone

from .models import Payment

NAIROBI = ZoneInfo('Africa/Nairobi')


def _totals(qs):
    row = qs.aggregate(n=Count('id'), total=Sum('amount'))
    return {'count': row['n'] or 0, 'amount': row['total'] or 0}


def _block(sandbox, now):
    start_today = datetime.combine(now.astimezone(NAIROBI).date(), time.min, tzinfo=NAIROBI)
    paid = Payment.objects.filter(status='paid', sandbox=sandbox)
    days = []
    rows = (paid.filter(paid_at__gte=start_today - timedelta(days=13)).annotate(day=TruncDate('paid_at', tzinfo=NAIROBI))
            .values('day').annotate(n=Count('id'), total=Sum('amount')))
    by_day = {r['day']: r for r in rows}
    for back in range(14):
        d = (start_today - timedelta(days=back)).date()
        r = by_day.get(d)
        days.append({'day': d, 'count': r['n'] if r else 0, 'amount': r['total'] if r else 0})
    return {
        'today': _totals(paid.filter(paid_at__gte=start_today)),
        'week': _totals(paid.filter(paid_at__gte=start_today - timedelta(days=6))),
        'month': _totals(paid.filter(paid_at__gte=start_today - timedelta(days=29))),
        'all': _totals(paid),
        'modules': _totals(paid.filter(product='module')),
        'all_pass': _totals(paid.filter(product='all')),
        'days': days,
    }


def sales_summary(now=None):
    now = now or timezone.now()
    return {
        'live': _block(False, now),
        'test': _block(True, now),
        'review': Payment.objects.filter(status='review').count(),
        'stuck': Payment.objects.filter(status='pending', created_at__lt=now - timedelta(minutes=15)).count(),
    }
