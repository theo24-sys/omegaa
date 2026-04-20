from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import ChatSession, ChatMessage
from payments.models import Payment, UserSubscription
from dashboard.views import first_time_verification_required

User = get_user_model()

@first_time_verification_required
@login_required
def inbox(request):
    sessions = ChatSession.objects.filter(participants=request.user).prefetch_related('participants', 'messages')
    
    # Optional enhancement: flag Pro messages if the user is a Househelp receiving from an Employer
    return render(request, 'chat/inbox.html', {'sessions': sessions})

@first_time_verification_required
@login_required
def chat_detail(request, session_id):
    session = get_object_or_404(ChatSession, id=session_id)
    if request.user not in session.participants.all() and not request.user.is_superuser:
        messages.error(request, "You do not have permission to view this chat.")
        return redirect('chat:inbox')
        
    chat_messages = session.messages.all()
    session.messages.exclude(sender=request.user).update(is_read=True)
    other_user = session.get_other_participant(request.user)
    
    if request.method == 'POST':
        text = request.POST.get('text')
        if text:
            # Strict Plan Enforcement (Chat)
            features = UserSubscription.get_active_features(request.user)
            if request.user.user_type == 'employer' and not request.user.is_superuser:
                if features.chat_message_limit > 0:
                    msg_count = ChatMessage.objects.filter(sender=request.user).count()
                    if msg_count >= features.chat_message_limit:
                        messages.warning(request, f"Your {features.name} allows {features.chat_message_limit} messages. Upgrade your plan for unlimited communication!")
                        return redirect('payments:payment_plans')
            
            msg = ChatMessage.objects.create(session=session, sender=request.user, text=text)
            session.updated_at = timezone.now()
            session.save()

            # Notify the other participant by SMS
            from notifications.utils import create_notification
            other_user = session.get_other_participant(request.user)
            create_notification(
                recipient=other_user,
                notification_type='chat_message',
                title=f"New message from {request.user.get_full_name() or request.user.username}",
                message=text[:50] + ("..." if len(text) > 50 else ""),
                related_object=msg,
                send_sms=True
            )
            
            return redirect('chat:chat_detail', session_id=session.id)
            
    # Handle badges for UI
    features = UserSubscription.get_active_features(request.user)
    is_gold = features.name == "Gold Plan" if features else False
    is_standard = features.name == "Standard Plan" if features else False
    
    return render(request, 'chat/detail.html', {
        'session': session,
        'chat_messages': chat_messages,
        'other_user': other_user,
        'is_gold': is_gold,
        'is_standard': is_standard
    })

@first_time_verification_required
@login_required
def video_interview(request, session_id):
    session = get_object_or_404(ChatSession, id=session_id)
    if request.user not in session.participants.all() and not request.user.is_superuser:
        messages.error(request, "You do not have permission to join this interview.")
        return redirect('chat:inbox')

    # Strict Plan Enforcement (Video)
    features = UserSubscription.get_active_features(request.user)
    if not request.user.is_superuser and request.user.user_type == 'employer':
        if not features.can_use_video:
            messages.warning(request, f"Video Interviewing is not available on the {features.name}. Upgrade to Standard or Gold to start interviewing today!")
            return redirect('payments:payment_plans')

    # Determine time limit in seconds
    time_limit = features.video_call_limit_mins * 60 if features else 0
    is_gold = features.name == "Gold Plan" if features else False
        
    # Mark interview as active
    session.interview_active_until = timezone.now() + timezone.timedelta(minutes=60)
    session.save()

    # SMS Alert for Video Interview
    from notifications.utils import create_notification
    other_user = session.get_other_participant(request.user)
    create_notification(
        recipient=other_user,
        notification_type='video_interview',
        title="Immediate Interview Invitation",
        message=f"{request.user.get_full_name() or request.user.username} is waiting for you in the video interview room! Join now on Charlady.",
        related_object=session,
        send_sms=True
    )
    
    return render(request, 'chat/video_call.html', {
        'session': session,
        'room_name': f"Charlady_Interview_{session.id}",
        'time_limit': time_limit,
        'is_gold': is_gold
    })

@login_required
def chat_messages_fragment(request, session_id):
    session = get_object_or_404(ChatSession, id=session_id)
    if request.user not in session.participants.all():
        return render(request, 'chat/error_fragment.html', {'error': 'Forbidden'})
    
    chat_messages = session.messages.all()
    # Mark as read since They are viewing the live fragment
    session.messages.exclude(sender=request.user).update(is_read=True)
    
    return render(request, 'chat/messages_fragment.html', {
        'chat_messages': chat_messages,
        'session': session
    })

@login_required
def check_invite(request):
    """
    Checks if there's an active interview call for the current user.
    Only returns HTML if a call is active.
    """
    active_session = ChatSession.objects.filter(
        participants=request.user,
        interview_active_until__gt=timezone.now()
    ).first()
    
    if active_session:
        other_user = active_session.get_other_participant(request.user)
        # Check if the user has ALREADY joined or if they are the one who started it
        # Since employers usually start, workers get the invite.
        return render(request, 'chat/call_invite_modal.html', {
            'session': active_session,
            'other_user': other_user
        })
    
    return render(request, 'chat/empty.html')

@first_time_verification_required
@login_required
def start_chat(request, user_id):
    target_user = get_object_or_404(User, id=user_id)
    
    if target_user == request.user:
        return redirect('chat:inbox')
        
    session = ChatSession.objects.filter(participants=request.user).filter(participants=target_user).first()
    
    if not session:
        # Strict Plan Enforcement (New Chat)
        features = UserSubscription.get_active_features(request.user)
        if request.user.user_type == 'employer' and not request.user.is_superuser:
            if features.chat_conversation_limit > 0:
                total_sessions = ChatSession.objects.filter(participants=request.user).count()
                if total_sessions >= features.chat_conversation_limit:
                    messages.warning(request, f"Your {features.name} restricts you to {features.chat_conversation_limit} active conversations. Upgrade for unlimited networking!")
                    return redirect('payments:payment_plans')
                
        session = ChatSession.objects.create()
        session.participants.add(request.user, target_user)
        
    return redirect('chat:chat_detail', session_id=session.id)
