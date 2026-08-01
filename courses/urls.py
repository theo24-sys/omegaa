from django.urls import path
from . import views

urlpatterns = [
    path('', views.course_list, name='course_list'),
    path('<int:course_id>/', views.course_detail, name='course_detail'),
    path('<int:course_id>/lesson/<int:lesson_id>/', views.lesson_detail, name='lesson_detail'),
    path('<int:course_id>/quiz/<int:lesson_id>/', views.course_quiz, name='lesson_quiz'),
    path('<int:course_id>/quiz/', views.course_quiz, name='course_quiz'),
    path('<int:course_id>/complete/', views.complete_course, name='complete_course'),
    path('seed/', views.seed_courses_view, name='seed_courses'),
]
