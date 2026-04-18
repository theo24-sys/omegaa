from django.urls import path
from . import views

app_name = 'reviews'

urlpatterns = [
    # Public review views
    path('user/<int:user_id>/', views.user_reviews, name='user_reviews'),
    path('user/<int:user_id>/create/', views.create_review, name='create_review'),
    path('<int:pk>/', views.ReviewView.as_view(), name='review'),
    
    # Review management
    path('<int:review_id>/edit/', views.edit_review, name='edit_review'),
    path('<int:review_id>/delete/', views.delete_review, name='delete_review'),
    
    # Admin moderation
    path('admin/reviews/', views.admin_reviews, name='admin_reviews'),
    path('admin/reviews/<int:review_id>/flag/', views.flag_review, name='flag_review'),
]