from django.urls import path
from . import views  # ← THIS WAS MISSING

app_name = 'reviews'

urlpatterns = [
    path('user/<int:user_id>/', views.user_reviews, name='user_reviews'),
    path('user/<int:user_id>/create/', views.create_review, name='create_review'),
    path('<int:pk>/', views.ReviewView.as_view(), name='review'),
]