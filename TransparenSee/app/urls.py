from django.urls import path
from .views import *
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('home', HomeTemplateView.as_view(), name='home'),
    path('student/', StudentDashboardView.as_view(), name='student_dashboard'),
    path('officer/treasurer/', TreasurerDashboardView.as_view(), name='treasurer_dashboard'),
    path('officer/auditor/', AuditorDashboardView.as_view(), name='auditor_dashboard'),
    path('officer/president/', PresidentDashboardView.as_view(), name='president_dashboard'),
    path('adviser/', AdviserDashboardView.as_view(), name='adviser_dashboard'),
    path('campus-admin/', CampusAdminDashboardView.as_view(), name='campus_admin_dashboard'),
    path('campus-admin/user-role/', CampusAdminUserRolesView.as_view(), name='campus_admin_user_role'),
    path('campus-admin/create-adviser', CreateAdviserView.as_view(), name='campus_admin_create_adviser'),
    path('campus-admin/create-officer', CreateOfficerView.as_view(), name='campus_admin_create_officer'),
    path('campus-admin/update-adviser/<int:pk>/', UpdateAdviserView.as_view(), name='campus_admin_update_adviser'),
    path('superadmin/', SuperAdminView.as_view(), name='superadmin_dashboard'),
    path('superadmin/user-role', UserRolesView.as_view(), name='superadmin_user_role'),
    path('superadmin/create-campus-admin', CreateCampusAdminView.as_view(), name='superadmin_create_campus_admin'),
    

    
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)