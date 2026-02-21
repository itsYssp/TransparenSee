from django.urls import path
from .views import *
from django.conf import settings
from django.conf.urls.static import static
urlpatterns = [
    path('home', HomeTemplateView.as_view(), name='home'),
    path('student/', StudentDashboardTemplate.as_view(), name='student_dashboard'),
    path('officer/', OfficerDashboardTemplate.as_view(), name='officer_dashboard'),
    
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)