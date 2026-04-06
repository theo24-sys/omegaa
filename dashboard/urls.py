from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_home, name='dashboard_home'),
    path('users/', views.dashboard_users, name='dashboard_users'),
    path('jobs/', views.dashboard_jobs, name='dashboard_jobs'),
    path('applications/', views.dashboard_applications, name='dashboard_applications'),
    path('stats/', views.dashboard_stats, name='dashboard_stats'),
    path('user/', views.user_dashboard, name='user_dashboard'),
    path('housekeeper/', views.housekeeper_dashboard, name='housekeeper_dashboard'),
    path('employer/', views.employer_dashboard, name='employer_dashboard'),
]