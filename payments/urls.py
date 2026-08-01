from django.urls import path
from . import views, admin_views

app_name = 'payments'

urlpatterns = [
    path('plans/', views.payment_plans, name='payment_plans'),
    path('checkout/<int:plan_id>/', views.checkout, name='checkout'),
    path('course-checkout/<int:course_id>/', views.course_checkout, name='course_checkout'),
    path('mpesa/<int:payment_id>/', views.mpesa_payment, name='mpesa_payment'),
    path('retry/<int:payment_id>/', views.retry_payment, name='retry_payment'),
    path('failed/<int:payment_id>/', views.payment_failed, name='payment_failed'),
    path('contribution/pay/<int:contribution_id>/', views.pay_contribution, name='pay_contribution'),
    path('contributions/', views.contribution_list, name='contribution_list'),
    path('mpesa/callback/', views.mpesa_callback, name='mpesa_callback'),
    path('status/<int:payment_id>/', views.check_payment_status, name='check_payment_status'),
    path('verification-submitted/<int:payment_id>/', views.payment_verification_submitted, name='payment_verification_submitted'),
    path('detail/<int:payment_id>/', views.payment_detail, name='payment_detail'),
    path('history/', views.payment_history, name='payment_history'),
    path('job-checkout/<int:job_id>/', views.job_checkout, name='job_checkout'),
    
    # Admin URLs
    path('admin/pending/', admin_views.pending_payments, name='admin_pending_payments'),
    path('admin/verify/<int:payment_id>/', admin_views.verify_payment, name='admin_verify_payment'),
    path('admin/all/', admin_views.all_payments, name='admin_all_payments'),
]

