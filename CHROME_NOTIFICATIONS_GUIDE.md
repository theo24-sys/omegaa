# Chrome Notifications Implementation Guide

## Overview

This guide describes the Chrome browser push notification system implemented for Charlady. Users can now receive browser notifications for job applications, messages, reviews, and system alerts.

## Features

### 1. **Permission Request**
- Users see a beautiful gradient banner after 3 seconds of page load
- Banner explains benefits: "Stay updated with job offers and messages"
- Users can enable or dismiss the notification request
- System respects browser's permission state

### 2. **Service Worker Registration**
- Automatically registers `/sw.js` as the service worker
- Handles background push notifications
- Manages notification lifecycle and interactions

### 3. **Browser Notifications**
- Desktop notifications with Charlady branding
- Custom icons and badges
- Click-to-navigate functionality
- Close event tracking

### 4. **Analytics & Tracking**
- Track permission granted/denied events
- Track notification clicks and closes
- Monitor browser types and user engagement
- Backend logging for debugging

### 5. **PushAlert Integration**
- Existing PushAlert service continues to work
- New system coexists with PushAlert
- Dual notification delivery for better reach

## Files Modified

### Frontend Files

| File | Changes |
|------|---------|
| `static/js/notifications.js` | New notification manager class |
| `templates/base.html` | Include notifications.js script |
| `templates/sw.js` | Enhanced service worker |
| `static/css/animations.css` | Added slideDown/slideUp animations |

### Backend Files

| File | Changes |
|------|---------|
| `notifications/views.py` | Added analytics endpoints |
| `notifications/urls.py` | Added API routes for analytics |

## How It Works

### User Journey

```
User visits Charlady
    ↓
Page loads (3-second delay)
    ↓
Permission banner shown
    ↓
User clicks "Enable" or "Dismiss"
    ↓
Permission granted → Service Worker registered
    ↓
User can receive notifications
```

### Notification Flow

```
Backend creates notification
    ↓
PushAlert broadcasts notification
    ↓
Browser receives notification
    ↓
Notification appears on desktop
    ↓
User clicks notification
    ↓
Page navigates to relevant content
    ↓
Analytics tracked
```

## JavaScript API

### NotificationManager Class

```javascript
const notificationManager = window.notificationManager;

// Get permission status
const permission = notificationManager.getNotificationPermission();
// Returns: 'granted', 'denied', or 'default'

// Request permission (shows browser dialog)
await notificationManager.requestPermission();

// Send notification
notificationManager.sendNotification('New Job Offer!', {
    body: 'A new job matching your skills',
    tag: 'job-notification',
    url: '/jobs/123/'
});

// Register service worker
await notificationManager.registerServiceWorker();

// Show permission banner
notificationManager.showNotificationBanner();
```

### Sending Notifications from Backend

```python
from notifications.utils import create_notification

# Create an in-app notification
create_notification(
    recipient=user,
    notification_type=Notification.TYPE_JOB_APPLICATION,
    title="New Job Application",
    message=f"You received a new application for '{job.title}'",
    related_object=application,
    send_sms=True  # Optional SMS
)

# For push notifications, use PushAlert API
```

## Browser Support

### Supported Browsers
- ✅ Chrome/Chromium (desktop & Android)
- ✅ Firefox (desktop & Android)
- ✅ Edge
- ✅ Brave
- ✅ Opera

### Fallback
- Safari: Uses in-app notifications only
- IE: Not supported

## API Endpoints

### Permission Tracking
```
POST /notifications/api/permission/

Body:
{
    "action": "permission_granted" | "permission_denied",
    "browser": "Chrome" | "Firefox" | "Safari" | etc
}

Response:
{
    "status": "success",
    "message": "Analytics recorded"
}
```

### Event Tracking
```
POST /notifications/api/event/

Body:
{
    "action": "notification_clicked" | "notification_closed",
    "title": "Notification title",
    "timestamp": "2026-04-19T10:30:00Z"
}

Response:
{
    "status": "success",
    "message": "Event recorded"
}
```

## Configuration

### Environment Variables
No additional environment variables required. The system uses existing Django settings.

### Settings
Check `housekeeper_connect/settings.py` - no special notification settings needed.

### Service Worker Cache
The service worker automatically caches important resources for offline functionality.

## Testing

### Test Permission Request
1. Open DevTools (F12)
2. Go to Console tab
3. Run: `notificationManager.requestPermission()`
4. Browser will show permission dialog

### Test Notification
```javascript
// In console
notificationManager.sendNotification('Test Notification', {
    body: 'This is a test notification',
    icon: '/static/img/logo.png'
});
```

### Test Service Worker
```javascript
// Check if registered
navigator.serviceWorker.ready.then(reg => {
    console.log('Service Worker ready:', reg);
});

// Send message to service worker
if (navigator.serviceWorker.controller) {
    navigator.serviceWorker.controller.postMessage({
        type: 'SEND_NOTIFICATION',
        title: 'Test from Service Worker',
        options: { body: 'Testing SW notifications' }
    });
}
```

## Monitoring & Logging

### Browser Console
- Permission status logged on page load
- Service Worker registration status
- Notification events logged
- Errors and warnings clearly marked

### Server Logs
```bash
# View notification events
tail -f logs/django.log | grep -i "notification"

# Sample log entries
INFO: Notification permission event - User: 123, Action: permission_granted, Browser: Chrome
INFO: Notification event - User: 123, Action: notification_clicked, Title: New Job
INFO: Didit verification completed - User: 123
```

## Troubleshooting

### Permissions Not Showing

**Issue**: Permission banner doesn't appear
**Solutions**:
1. Clear browser cache and cookies
2. Check console for JavaScript errors
3. Ensure notifications.js is loaded (DevTools → Sources)
4. Check browser notification settings

### Notifications Not Appearing

**Issue**: Notifications enabled but not showing
**Solutions**:
1. Check browser notification settings: `chrome://settings/content/notifications`
2. Ensure Charlady is in allowed list
3. Check that notifications.js is loaded
4. Service Worker may need re-registration

### Service Worker Not Registering

**Issue**: Service Worker registration fails
**Solutions**:
1. Open DevTools → Application → Service Workers
2. Check for registration errors
3. Ensure `/sw.js` is accessible and valid
4. Check browser console for errors

### Permission Denied

**Issue**: User previously denied notifications
**Solutions**:
1. User must go to browser settings to re-enable
2. For Chrome: `chrome://settings/content/notifications`
3. Find Charlady and change to "Allow"
4. Refresh page to see permission restored

## Performance Considerations

- **Service Worker**: ~5KB gzipped
- **Notifications.js**: ~8KB gzipped
- **Initial load**: Minimal impact (deferred loading)
- **Memory**: Low overhead, runs in background

## Security

### CSRF Protection
- All POST requests include CSRF token
- Token obtained from Django cookies
- Validated on backend

### Signature Verification
- Service Worker validates push events
- Prevents unauthorized notifications

### Data Privacy
- No sensitive data in notifications
- Analytics only tracks events, not content
- User data never transmitted in notifications

## Future Enhancements

1. **Notification Preferences**
   - Allow users to customize notification types
   - Quiet hours settings
   - Sound/vibration preferences

2. **Advanced Targeting**
   - Send notifications to specific user groups
   - Scheduled notifications
   - Template-based notifications

3. **Rich Notifications**
   - Images in notifications
   - Action buttons
   - Deep linking to app features

4. **Analytics Dashboard**
   - Admin view of notification stats
   - Delivery rates
   - User engagement metrics

## Rollout Checklist

- [x] Service Worker implementation
- [x] Notification Manager class
- [x] Analytics endpoints
- [x] CSS animations
- [x] Documentation
- [ ] User testing
- [ ] Monitor error rates
- [ ] Adjust based on feedback

## Support

For issues or questions:
1. Check browser console for errors
2. Check server logs for backend errors
3. Verify service worker in DevTools
4. Test with simple notification first
5. Contact development team with error logs
