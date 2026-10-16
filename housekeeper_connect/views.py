# housekeeper_connect/views.py
from django.db import connection
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from payments.models import Payment
from notifications.models import Notification  # correct import

def home(request):
    unread_count = 0
    if request.user.is_authenticated:
        # Use 'recipient' — that's the correct ForeignKey field in your model
        unread_count = Notification.objects.filter(
            recipient=request.user,
            is_read=False
        ).count()
    
    return render(request, 'home.html', {
        'unread_count': unread_count
    })

def terms(request):
    return render(request, 'pages/terms.html')

def privacy(request):
    return render(request, 'pages/privacy.html')


def page_not_found(request, exception):
    return render(request, '404.html', status=404)


def health(request):
    """Return a lightweight liveness/readiness response for deployment probes."""
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
            cursor.fetchone()
        return JsonResponse({'status': 'ok', 'database': 'ok', 'timestamp': timezone.now().isoformat()})
    except Exception:
        return JsonResponse({'status': 'error', 'database': 'unavailable'}, status=503)


def health_payments(request):
    """Expose non-sensitive payment queue counts for operational monitoring."""
    try:
        return JsonResponse({
            'status': 'ok',
            'pending': Payment.objects.filter(status='pending').count(),
            'verification_submitted': Payment.objects.filter(status='verification_submitted').count(),
            'timestamp': timezone.now().isoformat(),
        })
    except Exception:
        return JsonResponse({'status': 'error'}, status=503)


def health_database(request):
    return health(request)


def health_celery(request):
    try:
        from celery import current_app
        workers = current_app.control.ping(timeout=1.0)
        if not workers:
            return JsonResponse({'status': 'error', 'celery': 'no_workers'}, status=503)
        return JsonResponse({'status': 'ok', 'celery': 'ok', 'workers': len(workers)})
    except Exception:
        return JsonResponse({'status': 'error', 'celery': 'unavailable'}, status=503)