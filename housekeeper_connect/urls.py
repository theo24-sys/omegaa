# urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.views.generic import TemplateView
from django.conf.urls.static import static
from . import views  # import your views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),  # ← changed to use the function view
    path('accounts/', include('accounts.urls')),
    path('jobs/', include('jobs.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('notifications/', include('notifications.urls')),
    path('reviews/', include(('reviews.urls', 'reviews'), namespace='reviews')),
    path('contact-admin/', TemplateView.as_view(template_name='contact_admin.html'), name='contact_admin'),
    path('payments/', include('payments.urls')),
    path('blog/', include('blog.urls')),
    path('courses/', include('courses.urls')),
    path('chat/', include('chat.urls')),
    path('terms/', views.terms, name='terms'),
    path('privacy/', views.privacy, name='privacy'),
    # Service Worker for PushAlert
    path('sw.js', TemplateView.as_view(template_name='sw.js', content_type='application/javascript'), name='service_worker'),
]

# Unconditionally serve static and media files (Patch for Railway filesystem ephemeral issues)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)