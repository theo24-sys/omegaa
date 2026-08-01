import hmac
import hashlib
import logging
import json
import requests
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
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
    Directly create Didit session and redirect to verification UI.
    """
    user = request.user
    
    # Check if user is a housekeeper
    if user.user_type != 'househelp':
        messages.error(request, "Identity verification is only required for housekeepers.")
        return redirect('home')
    
    # If already verified, redirect to dashboard
    if user.has_completed_first_verification:
        messages.info(request, "You have already completed identity verification.")
        return redirect('dashboard:housekeeper_dashboard')
    
    # Create Didit session directly
    return _create_didit_session(request, user)


def _create_didit_session(request, user):
    """
    Internal function to create a Didit session and redirect user to verification UI.
    """
    # Payload for session creation
    # Documentation: https://docs.didit.me
    payload = {
        "vendor_data": str(user.id),
        "workflow_id": DIDIT_WORKFLOW_ID,
        "callback": request.build_absolute_uri(reverse('dashboard:housekeeper_dashboard' if user.user_type == 'househelp' else 'dashboard:employer_dashboard')),
        "features": ["identity_document", "face_match"] # Adjust based on your workflow needs
    }
    
    # Ensure we always fetch the latest key from settings in case of hot-reload cache issues
    current_api_key = getattr(settings, 'DIDIT_API_KEY', DIDIT_API_KEY)
    
    headers = {
        "x-api-key": current_api_key,
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(
            f"{DIDIT_BASE_URL}/session/", 
            json=payload, 
            headers=headers,
            timeout=10
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
            # Store that this is a first-time verification attempt
            request.session['didit_verification_in_progress'] = True
            logger.info(f"Didit session created for user {user.id}: {data.get('id')}")
            return redirect(verification_url)
        else:
            logger.error(f"Didit session created but no URL returned for user {user.id}")
            messages.error(request, "Error initiating verification: No URL returned. Please try again later.")
            return redirect('home')
            
    except Exception as e:
        logger.error(f"Failed to initiate Didit verification for user {user.id}: {e}")
        messages.error(request, f"Verification service is temporarily unavailable. ({str(e)})")
        return redirect('home')

@csrf_exempt
def didit_webhook(request):
    """
    Handles incoming status updates from Didit.
    """
    if request.method != 'POST':
        return HttpResponse(status=405)
        
    # ─── SECURITY: Webhook Signature Verification ───────────────────────────
    signature = request.headers.get('x-didit-signature') or request.headers.get('X-Signature')
    
    if DIDIT_WEBHOOK_SECRET and signature:
        try:
            expected_signature = hmac.new(
                DIDIT_WEBHOOK_SECRET.encode('utf-8'),
                request.body,
                hashlib.sha256
            ).hexdigest()
            
            if not hmac.compare_digest(expected_signature, signature):
                logger.error("Invalid Didit webhook signature")
                if not settings.DEBUG:
                    return HttpResponse("Invalid signature", status=401)
        except Exception as e:
            logger.error(f"Didit Webhook: Signature verification error: {e}")
    elif DIDIT_WEBHOOK_SECRET and not signature:
        logger.warning("Didit Webhook: Secret set but signature missing from headers")
        # Don't block in production if we're debugging connectivity, but log it
    # ────────────────────────────────────────────────────────────────────────
    # ────────────────────────────────────────────────────────────────────────
    
    try:
        data = json.loads(request.body)
        logger.info(f"Incoming Didit webhook payload: {json.dumps(data)}")
        
        # Didit V3 can send nested 'session' object or flat payload
        session_data = data.get('session', data) 
        
        # Extract fields from nested or flat structure
        session_id = session_data.get('id') or data.get('session_id')
        vendor_id = session_data.get('vendor_data') or session_data.get('vendor_id') or data.get('metadata', {}).get('user_id')
        status = session_data.get('status') or data.get('status')
        
        # ─── INPUT VALIDATION ──────────────────────────────────────────────
        if not vendor_id:
            logger.warning(f"Missing vendor_id/user_id in Didit webhook. Payload keys: {list(data.keys())}")
            return JsonResponse({"error": "missing vendor_id"}, status=400)
        
        if not status:
            logger.warning(f"Missing status in Didit webhook. Payload keys: {list(data.keys())}")
            return JsonResponse({"error": "missing status"}, status=400)
        # ────────────────────────────────────────────────────────────────────
            
        user = CustomUser.objects.filter(id=vendor_id).first()
        if not user:
            logger.warning(f"User {vendor_id} not found in Didit webhook")
            return JsonResponse({"error": "user not found"}, status=404)
            
        # ─── UPDATE STATUS BASED ON VERIFICATION RESULT ───────────────────
        # Use case-insensitive comparison for status
        status_upper = status.upper()
        logger.info(f"Processing Didit webhook for user {user.id} with status: {status_upper}")

        if status_upper in ['SUCCESS', 'APPROVED', 'COMPLETED']:
            user.didit_verification_status = 'completed'
            user.is_verified = True
            user.badge_verified_id = True
            user.has_completed_first_verification = True  # Mark first verification as complete
            user.save()
            logger.info(f"User {user.id} verified successfully via Didit (Status: {status_upper})")
        elif status_upper in ['FAILED', 'DECLINED']:
            user.didit_verification_status = 'failed'
            user.save()
            logger.warning(f"User {user.id} verification FAILED via Didit (Status: {status_upper})")
        elif status_upper == 'EXPIRED':
            user.didit_verification_status = 'expired'
            user.save()
            logger.warning(f"User {user.id} Didit verification session expired")
        elif status_upper in ['PENDING', 'IN_PROGRESS', 'IN_REVIEW']:
            user.didit_verification_status = status_upper.lower()
            user.save()
        else:
            logger.warning(f"Unhandled Didit status: {status_upper}")
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
