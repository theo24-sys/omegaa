import json
import logging
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
        response = requests.post(f"{DIDIT_BASE_URL}/sessions", json=payload, headers=headers)
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
        
    # verify signature (recommended)
    # x-webhook-secret header check could be added here
    
    try:
        data = json.loads(request.body)
        event_type = data.get('event')
        session_data = data.get('session', {})
        session_id = session_data.get('id')
        vendor_id = session_data.get('vendor_id')
        status = session_data.get('status')
        
        if not vendor_id:
            return JsonResponse({"error": "missing vendor_id"}, status=400)
            
        user = CustomUser.objects.filter(id=vendor_id).first()
        if not user:
            return JsonResponse({"error": "user not found"}, status=404)
            
        # Update status based on event
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
        else:
            user.didit_verification_status = 'pending'
            user.save()
            
        return JsonResponse({"status": "received"})
        
    except Exception as e:
        logger.error(f"Error processing Didit webhook: {e}")
        return JsonResponse({"error": str(e)}, status=500)
