from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import ChatSession, ChatMessage
from payments.models import Payment

User = get_user_model()

@login_required
def inbox(request):
    sessions = ChatSession.objects.filter(participants=request.user).prefetch_related('participants', 'messages')
    
    # Optional enhancement: flag Pro messages if the user is a Househelp receiving from an Employer
    return render(request, 'chat/inbox.html', {'sessions': sessions})

@login_required
def chat_detail(request, session_id):
    session = get_object_or_404(ChatSession, id=session_id)
    if request.user not in session.participants.all() and not request.user.is_superuser:
        messages.error(request, "You do not have permission to view this chat.")
        return redirect('inbox')
        
    chat_messages = session.messages.all()
    session.messages.exclude(sender=request.user).update(is_read=True)
    other_user = session.get_other_participant(request.user)
    
    if request.method == 'POST':
        text = request.POST.get('text')
        if text:
            # Plan Restrictions Enforcement
            if request.user.user_type == 'employer' and not request.user.is_verified and not request.user.is_superuser:
                # Free Limit: Max 5 total messages across all chats
                msg_count = ChatMessage.objects.filter(sender=request.user).count()
                if msg_count >= 5:
                    messages.warning(request, "You have reached your Free Plan limit. Please upgrade to Standard or Gold to continue chatting seamlessly!")
                    return redirect('payment_plans')
            
            ChatMessage.objects.create(session=session, sender=request.user, text=text)
            session.updated_at = timezone.now()
            session.save()
            return redirect('chat_detail', session_id=session.id)
            
    is_gold = False
    is_standard = False
    if request.user.is_authenticated:
        # Check if they have the 1000 KES active plan (Gold)
        is_gold = Payment.objects.filter(user=request.user, status='completed', plan__price=1000).exists()
        # Check if they have the 300 KES active plan (Standard)
        is_standard = Payment.objects.filter(user=request.user, status='completed', plan__price=300).exists()
    
    return render(request, 'chat/detail.html', {
        'session': session,
        'chat_messages': chat_messages,
        'other_user': other_user,
        'is_gold': is_gold,
        'is_standard': is_standard
    })

@login_required
def video_interview(request, session_id):
    session = get_object_or_404(ChatSession, id=session_id)
    if request.user not in session.participants.all() and not request.user.is_superuser:
        messages.error(request, "You do not have permission to join this interview.")
        return redirect('inbox')

    # Plan Restrictions
    is_gold = False
    is_standard = False
    if not request.user.is_superuser:
        is_gold = Payment.objects.filter(user=request.user, status='completed', plan__price=1000).exists()
        is_standard = Payment.objects.filter(user=request.user, status='completed', plan__price=300).exists()
        
        # If user is employer and not verified, block them
        if request.user.user_type == 'employer' and not is_gold and not is_standard:
            messages.warning(request, "Video Interviewing is a premium feature. Upgrade to Standard or Gold to start interviewing today!")
            return redirect('payment_plans')
    else:
        is_gold = True # Admins get gold access

    # Determine time limit in seconds
    time_limit = 0 # 0 means unlimited
    if is_standard and not is_gold:
        time_limit = 15 * 60 # 15 minutes
        
    # Mark interview as active for the next hour to alert the other party
    session.interview_active_until = timezone.now() + timezone.timedelta(minutes=60)
    session.save()
    
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

@login_required
def start_chat(request, user_id):
    target_user = get_object_or_404(User, id=user_id)
    
    if target_user == request.user:
        return redirect('inbox')
        
    session = ChatSession.objects.filter(participants=request.user).filter(participants=target_user).first()
    
    if not session:
        # Plan Restrictions Enforcement
        if request.user.user_type == 'employer' and not request.user.is_verified and not request.user.is_superuser:
            total_sessions = ChatSession.objects.filter(participants=request.user).count()
            if total_sessions >= 2:
                messages.warning(request, "Free Plan Restriction: You can only start 2 conversations. Please upgrade to securely message more professionals.")
                return redirect('payment_plans')
                
        session = ChatSession.objects.create()
        session.participants.add(request.user, target_user)
        
    return redirect('chat_detail', session_id=session.id)
