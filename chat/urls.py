from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('', views.inbox, name='inbox'),
    path('<int:session_id>/', views.chat_detail, name='chat_detail'),
    path('<int:session_id>/messages/', views.chat_messages_fragment, name='messages_fragment'),
    path('check-invite/', views.check_invite, name='check_invite'),
    path('interview/<int:session_id>/', views.video_interview, name='video_interview'),
    path('start/<int:user_id>/', views.start_chat, name='start_chat'),
]
