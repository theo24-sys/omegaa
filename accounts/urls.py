from django.urls import path
from django.contrib.auth import views as auth_views
from . import views, views_didit

urlpatterns = [
    path('api/kenya-locations.json', views.kenya_locations_json, name='kenya_locations_json'),
    path('signup/', views.signup, name='signup'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('profile/<int:user_id>/', views.profile_detail, name='profile_detail'),
    path('edit-profile/', views.edit_profile, name='edit_profile'),
    path('verify-email/<uidb64>/<token>/', views.verify_email, name='verify_email'),

    # Didit Identity Verification
    path('didit/verify/', views_didit.initiate_didit_verification, name='initiate_didit_verification'),
    path('didit/webhook/', views_didit.didit_webhook, name='didit_webhook'),

    # Password Reset URLs
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='registration/password_reset_form.html'), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='registration/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'), name='password_reset_complete'),
]