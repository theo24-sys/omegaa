import hmac
import hashlib
import logging
import json
import requests
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from .models import CustomUser

logger = logging.getLogger(__name__)

# DIDIT API CONFIG
DIDIT_BASE_URL = "https://verification.didit.me/v3"
DIDIT_APP_ID = getattr(settings, 'DIDIT_APP_ID', '')
DIDIT_API_KEY = getattr(settings, 'DIDIT_API_KEY', '')
DIDIT_WORKFLOW_ID = getattr(settings, 'DIDIT_WORKFLOW_ID', '')
DIDIT_WEBHOOK_SECRET = getattr(settings, 'DIDIT_WEBHOOK_SECRET', '')

@login_required
def initiate_didit_verification(request):
    """
    Creates a Didit session and redirects the user to the verification UI.
    """
    user = request.user
    
    # Payload for session creation
    # Documentation: https://docs.didit.me
    payload = {
        "vendor_id": str(user.id),
        "workflow_id": DIDIT_WORKFLOW_ID,
        "callback_url": request.build_absolute_uri(reverse('dashboard:housekeeper_dashboard' if user.user_type == 'househelp' else 'dashboard:employer_dashboard')),
        "features": ["identity_document", "face_match"] # Adjust based on your workflow needs
    }
    
    headers = {
        "x-api-key": DIDIT_API_KEY,
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(
            f"{DIDIT_BASE_URL}/sessions", 
            json=payload, 
            headers=headers,
            timeout=10 # Issue: Missing timeout
        )
        response.raise_for_status()
        data = response.json()
        
        # Store session ID
        user.didit_session_id = data.get('id')
        user.didit_verification_status = 'pending'
        user.save()
        
        # Redirect to Didit hosted UI
        verification_url = data.get('url')
        if verification_url:
            return redirect(verification_url)
        else:
            logger.error(f"Didit session created but no URL returned for user {user.id}")
            return HttpResponse("Error initiating verification. Please try again later.", status=500)
            
    except Exception as e:
        logger.error(f"Failed to initiate Didit verification for user {user.id}: {e}")
        return HttpResponse("Verification service is temporarily unavailable.", status=503)

@csrf_exempt
def didit_webhook(request):
    """
    Handles incoming status updates from Didit.
    """
    if request.method != 'POST':
        return HttpResponse(status=405)
        
    # ─── SECURITY: Webhook Signature Verification ───────────────────────────
    signature = request.headers.get('x-didit-signature')
    if not signature and not settings.DEBUG:
        logger.warning("Missing Didit signature header")
        return HttpResponse("Missing signature", status=401)
        
    if DIDIT_WEBHOOK_SECRET:
        expected_signature = hmac.new(
            DIDIT_WEBHOOK_SECRET.encode('utf-8'),
            request.body,
            hashlib.sha256
        ).hexdigest()
        
        if not hmac.compare_digest(expected_signature, signature):
            logger.error("Invalid Didit webhook signature")
            return HttpResponse("Invalid signature", status=401)
    # ────────────────────────────────────────────────────────────────────────
    
    try:
        data = json.loads(request.body)
        event_type = data.get('event')
        session_data = data.get('session', {})
        session_id = session_data.get('id')
        vendor_id = session_data.get('vendor_id')
        status = session_data.get('status')
        
        # ─── INPUT VALIDATION ──────────────────────────────────────────────
        if not vendor_id:
            logger.warning("Missing vendor_id in Didit webhook")
            return JsonResponse({"error": "missing vendor_id"}, status=400)
        
        if not status:
            logger.warning("Missing status in Didit webhook")
            return JsonResponse({"error": "missing status"}, status=400)
        # ────────────────────────────────────────────────────────────────────
            
        user = CustomUser.objects.filter(id=vendor_id).first()
        if not user:
            logger.warning(f"User {vendor_id} not found in Didit webhook")
            return JsonResponse({"error": "user not found"}, status=404)
            
        # ─── UPDATE STATUS BASED ON VERIFICATION RESULT ───────────────────
        # Detailed status handling
        if status == 'SUCCESS':
            user.didit_verification_status = 'completed'
            user.is_verified = True
            user.badge_verified_id = True
            user.save()
            logger.info(f"User {user.id} verified successfully via Didit")
        elif status == 'FAILED':
            user.didit_verification_status = 'failed'
            user.save()
            logger.warning(f"User {user.id} verification FAILED via Didit")
        elif status == 'PENDING':
            user.didit_verification_status = 'pending'
            user.save()
        elif status == 'EXPIRED':
            user.didit_verification_status = 'expired'
            user.save()
            logger.warning(f"User {user.id} Didit verification session expired")
        else:
            logger.warning(f"Unknown Didit status: {status}")
            user.didit_verification_status = 'pending'
            user.save()
        # ────────────────────────────────────────────────────────────────────
            
        return JsonResponse({"status": "received"})
        
    except json.JSONDecodeError:
        logger.error("Invalid JSON in Didit webhook")
        return JsonResponse({"error": "invalid json"}, status=400)
    except CustomUser.DoesNotExist:
        logger.warning("User not found in Didit webhook handler")
        return JsonResponse({"error": "user not found"}, status=404)
    except Exception as e:
        logger.error(f"Error processing Didit webhook: {e}", exc_info=True)
        return JsonResponse({"error": "internal error"}, status=500)
