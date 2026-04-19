from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json
import logging
from .models import Notification

logger = logging.getLogger(__name__)

@login_required
def notification_list(request):
    notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')
    unread_count = notifications.filter(is_read=False).count()
    
    context = {
        'notifications': notifications,
        'unread_count': unread_count,
    }
    return render(request, 'notifications/notification_list.html', context)

@login_required
def mark_as_read(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
    notification.is_read = True
    notification.save()
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'status': 'success',
            'message': 'Marked as read'
        })
    
    return redirect('notifications:notification_list')

@login_required
def mark_all_as_read(request):
    Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'status': 'success',
            'message': 'All notifications marked as read'
        })
    
    return redirect('notifications:notification_list')

@login_required
def unread_count_badge(request):
    """
    Returns only the notification icon fragment for HTMX polling.
    """
    unread_count = Notification.objects.filter(recipient=request.user, is_read=False).count()
    return render(request, 'notifications/unread_badge_fragment.html', {'unread_count': unread_count})


# ────────────────────────────────────────────────
# Analytics & Tracking Views
# ────────────────────────────────────────────────

@login_required
@require_http_methods(["POST"])
def notification_permission_analytics(request):
    """Track notification permission events"""
    try:
        data = json.loads(request.body)
        action = data.get('action')
        browser = data.get('browser', 'Unknown')
        
        logger.info(f"Notification permission event - User: {request.user.id}, Action: {action}, Browser: {browser}")
        
        # Update user preference if permission granted
        if action == 'permission_granted':
            request.user.notification_preferences = {
                'browser_notifications_enabled': True,
                'browser': browser
            }
            request.user.save(update_fields=['notification_preferences'])
        
        return JsonResponse({
            'status': 'success',
            'message': 'Analytics recorded'
        })
    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid JSON'
        }, status=400)
    except Exception as e:
        logger.error(f"Error recording notification permission analytics: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': 'Failed to record analytics'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def notification_event_analytics(request):
    """Track notification events (click, close, etc)"""
    try:
        data = json.loads(request.body)
        action = data.get('action')
        title = data.get('title', 'Unknown')
        
        logger.info(f"Notification event - User: {request.user.id}, Action: {action}, Title: {title}")
        
        return JsonResponse({
            'status': 'success',
            'message': 'Event recorded'
        })
    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid JSON'
        }, status=400)
    except Exception as e:
        logger.error(f"Error recording notification event analytics: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': 'Failed to record event'
        }, status=500)