# First-Time Identity Verification Implementation

## Overview

This document describes the implementation of first-time identity verification for housekeepers using Didit KYC service. Housekeepers must complete identity verification before accessing their dashboard.

## Architecture

### Flow Diagram

```
Login/Dashboard Access
    ↓
first_time_verification_required decorator
    ↓
Has user completed verification?
    ├─ YES → Allow dashboard access
    └─ NO → Redirect to verification page
    ↓
Display first_verification_required.html
    ├─ User clicks "Start Verification"
    └─ User clicks "Return Home"
    ↓ (if Start Verification clicked)
POST to initiate_didit_verification
    ↓
_create_didit_session()
    ├─ Create Didit session
    ├─ Store session ID
    └─ Redirect to Didit
    ↓
Didit Verification Process
    ├─ User uploads ID
    ├─ User takes selfie
    └─ Didit processes verification
    ↓
Didit Webhook Callback
    ├─ POST to didit_webhook
    ├─ Verify webhook signature
    ├─ Update user status
    └─ Set has_completed_first_verification = True
    ↓
Redirect to Dashboard
```

## Components

### 1. Database Model

**File**: `accounts/models.py`

Added field to `CustomUser`:
```python
has_completed_first_verification = models.BooleanField(
    default=False,
    help_text="Whether user has completed first-time identity verification"
)
```

**Migration**: `0014_customuser_has_completed_first_verification.py`

Apply migration:
```bash
python manage.py migrate accounts
```

### 2. Decorator

**File**: `dashboard/views.py`

```python
def first_time_verification_required(view_func):
    """Decorator to ensure housekeeper has completed first-time Didit verification"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.user_type == 'househelp':
            if not request.user.has_completed_first_verification:
                messages.warning(request, 'Please complete identity verification to access your dashboard.')
                return redirect('accounts:initiate_didit_verification')
        return view_func(request, *args, **kwargs)
    return wrapper
```

**Applied to**:
- `housekeeper_dashboard` view

### 3. Authentication Views

**File**: `accounts/views.py`

Modified `login()` function to check verification status:
```python
# After successful login, check if househelp needs verification
if user.user_type == 'househelp' and not user.has_completed_first_verification:
    messages.info(request, 'Please complete identity verification to continue.')
    return redirect('accounts:initiate_didit_verification')
```

### 4. Didit Integration Views

**File**: `accounts/views_didit.py`

#### `initiate_didit_verification(request)`
- Two-step flow:
  - GET/initial access: Display template
  - POST: Create Didit session
- Validates user is housekeeper
- Checks if already verified
- Error handling with user-friendly messages

#### `_create_didit_session(request, user)`
- Internal function to create Didit session
- Calls Didit API
- Stores session ID in user model
- Redirects to Didit verification URL

#### `didit_webhook(request)` [Pre-existing]
- Handles Didit callbacks
- Verifies webhook signature
- Updates user status based on verification result
- Sets `has_completed_first_verification = True` on success

### 5. Verification Template

**File**: `templates/accounts/first_verification_required.html`

Features:
- Beautiful gradient UI with animations
- 3 feature cards (Quick & Easy, Secure & Safe, Build Trust)
- Requirements checklist
- Trust indicators section
- Form POST button for "Start Verification"
- Responsive design
- Didit branding

The form POSTs back to `initiate_didit_verification` which then creates the Didit session.

### 6. URL Routing

**File**: `accounts/urls.py`

Already configured (no changes needed):
```python
path('didit/verify/', views_didit.initiate_didit_verification, name='initiate_didit_verification'),
path('didit/webhook/', views_didit.didit_webhook, name='didit_webhook'),
```

## Configuration

### Required Settings

Add these to `housekeeper_connect/settings.py`:

```python
# Didit Identity Verification Configuration
DIDIT_APP_ID = os.getenv('DIDIT_APP_ID', '')
DIDIT_API_KEY = os.getenv('DIDIT_API_KEY', '')
DIDIT_WORKFLOW_ID = os.getenv('DIDIT_WORKFLOW_ID', '')
DIDIT_WEBHOOK_SECRET = os.getenv('DIDIT_WEBHOOK_SECRET', '')

# Didit API Base URL (do not change)
DIDIT_BASE_URL = "https://verification.didit.me/v3"
```

### Environment Variables

Create/update `.env` file:
```bash
# Didit Configuration
DIDIT_APP_ID=your_app_id
DIDIT_API_KEY=your_api_key
DIDIT_WORKFLOW_ID=your_workflow_id
DIDIT_WEBHOOK_SECRET=your_webhook_secret
```

### Obtaining Didit Credentials

1. Sign up at [Didit Dashboard](https://dashboard.didit.me)
2. Create a new application
3. Configure workflow for Kenya (ID verification + face match)
4. Copy credentials to environment variables
5. Set webhook URL to: `https://your-domain.com/accounts/didit/webhook/`

## Deployment Checklist

- [ ] Add Didit configuration environment variables
- [ ] Run migration: `python manage.py migrate accounts`
- [ ] Configure webhook URL in Didit dashboard
- [ ] Test flow in staging:
  1. Create housekeeper account
  2. Try to access dashboard
  3. Complete verification flow
  4. Verify dashboard access granted
- [ ] Monitor webhook logs for errors
- [ ] Set up alerts for failed verifications
- [ ] Test production deployment with test Didit account

## Testing

### Test Scenarios

1. **New Housekeeper Login**
   - Create new housekeeper account
   - Login
   - Should redirect to verification page
   - ✓ Page displays correctly

2. **Start Verification**
   - Click "Start Verification" button
   - Should redirect to Didit
   - ✓ Didit session created

3. **Complete Verification**
   - Complete Didit process
   - Should redirect to dashboard
   - ✓ `has_completed_first_verification` set to True

4. **Return Home**
   - Click "Return Home" on verification page
   - Should redirect to home
   - ✓ Can verify verification page again later

5. **Repeat Access**
   - Already verified user logs in
   - Should go straight to dashboard
   - ✓ No verification page shown

6. **Non-Housekeeper Access**
   - Employer tries to access housekeeper dashboard
   - Should be denied
   - ✓ Redirected with error message

### Manual Testing

```bash
# Access verification page
curl http://localhost:8000/accounts/didit/verify/

# Simulate webhook (requires CSRF token in production)
curl -X POST http://localhost:8000/accounts/didit/webhook/ \
  -H "Content-Type: application/json" \
  -H "x-didit-signature: <signature>" \
  -d '{...}'
```

## Security Considerations

### Webhook Signature Verification
- All Didit webhooks are verified using HMAC-SHA256
- Signature is in `x-didit-signature` header
- Secret key from `DIDIT_WEBHOOK_SECRET` environment variable
- Disabled only in DEBUG mode (development only)

### Session Management
- Didit session ID stored in user model
- Prevents token reuse
- Session expires after verification or timeout

### User Validation
- Only housekeepers can access verification
- Already verified users skip verification
- Employer accounts cannot access housekeeper verification

### Data Privacy
- User documents never stored on Charlady servers
- Didit handles all document processing
- Documents auto-deleted by Didit after processing
- Only verification status stored in database

## Troubleshooting

### Common Issues

**Issue**: Webhook not being called
- **Check**: Webhook URL configured in Didit dashboard
- **Check**: Firewall allows POST from Didit IP range
- **Check**: Django CSRF is configured correctly

**Issue**: Signature verification failing
- **Check**: `DIDIT_WEBHOOK_SECRET` matches Didit dashboard
- **Check**: Not in production with DEBUG=False (should use real secrets)

**Issue**: User stuck on verification page
- **Check**: Session properly created in Didit
- **Check**: Didit URL accessible from user's network
- **Check**: Browser allows redirects

**Issue**: `has_completed_first_verification` not updating
- **Check**: Webhook is being received (check logs)
- **Check**: Webhook status is 'SUCCESS'
- **Check**: Database migration applied

### Logs to Monitor

```python
# Check logs
tail -f logs/django.log | grep -i didit

# Look for:
# - "Didit session created for user"
# - "User verified successfully via Didit"
# - "Verification failed"
# - "Invalid Didit webhook signature"
```

## Monitoring

### Metrics to Track

1. **Verification Completion Rate**
   - Count of `has_completed_first_verification = True` housekeepers
   - Ratio of completed vs. attempted verifications

2. **Webhook Health**
   - Count of successful webhook deliveries
   - Count of failed webhook deliveries
   - Webhook processing time

3. **User Experience**
   - Time from seeing verification page to completion
   - Abandonment rate (users who don't complete)
   - Error rates by status code

### Alerts

Set up alerts for:
- Webhook signature verification failures
- Didit API timeouts/errors
- Users with pending verification for >24 hours
- Unusual verification failure patterns

## Future Enhancements

1. **Verification Status Dashboard**
   - Admin view of verification statuses
   - Export verification reports
   - Manual verification override

2. **Retry Logic**
   - Automatic retry for failed Didit calls
   - Exponential backoff
   - Max retry limits

3. **Verification History**
   - Track multiple verification attempts
   - Store verification timestamps
   - Document ID information (hashed)

4. **Notifications**
   - Email when verification completes
   - Email reminders for incomplete verifications
   - SMS notifications option

## References

- [Didit Documentation](https://docs.didit.me)
- [Django Decorators](https://docs.djangoproject.com/en/stable/topics/http/decorators/)
- [Django Signals](https://docs.djangoproject.com/en/stable/topics/signals/)
- [HMAC Verification](https://docs.python.org/3/library/hmac.html)
