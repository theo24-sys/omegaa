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
            
    is_pro = False
    if request.user.is_authenticated:
        # Check if they have the 1000 KES active plan (Gold)
        is_pro = Payment.objects.filter(user=request.user, status='completed', plan__price=1000).exists()
    
    return render(request, 'chat/detail.html', {
        'session': session,
        'chat_messages': chat_messages,
        'other_user': other_user,
        'is_pro': is_pro
    })

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
