from django.urls import path
from . import views

urlpatterns = [
    path('', views.inbox, name='inbox'),
    path('<int:session_id>/', views.chat_detail, name='chat_detail'),
    path('interview/<int:session_id>/', views.video_interview, name='video_interview'),
    path('start/<int:user_id>/', views.start_chat, name='start_chat'),
]
