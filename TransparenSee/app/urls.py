from django.urls import path
from .views import *
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('home', HomeTemplateView.as_view(), name='home'),
    path('student/', StudentDashboardTemplate.as_view(), name='student_dashboard'),
    path('officer/treasurer/', TreasurerDashboardTemplate.as_view(), name='treasurer_dashboard'),
    path('officer/auditor/', AuditorDashboardTemplate.as_view(), name='auditor_dashboard'),
    path('officer/president/', PresidentDashboardTemplate.as_view(), name='president_dashboard'),
    path('adviser/', AdviserDashboardTemplate.as_view(), name='adviser_dashboard'),
    path('campus_admin/', CampusAdminDashboardTemplate.as_view(), name='campus_admin_dashboard'),
    path('superadmin/', SuperAdminTemplate.as_view(), name='superadmin_dashboard'),
    path('superadmin/user-role', UserRolseTemplate.as_view(), name='superadmin_user_role'),
    path('superadmin/create-campus-admin', CreateCampusAdminTemplate.as_view(), name='superadmin_create_campus_admin'),


    
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)