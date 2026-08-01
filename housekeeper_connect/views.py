# housekeeper_connect/views.py
from django.shortcuts import render
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