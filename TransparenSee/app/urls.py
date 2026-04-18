from django.urls import path
from .views import *
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from app import views

urlpatterns = [
    path('home', HomeTemplateView.as_view(), name='home'),
    path('student/', StudentDashboardView.as_view(), name='student_dashboard'),
    path('student/profile/', StudentProfileView.as_view(), name='student_profile'),
    path('password-change/', auth_views.PasswordChangeView.as_view(template_name='app/student/student_profile.html',success_url='/profile/'), name='password_change'),
    path('chat', ChatView.as_view(), name='chat'),
    path('chat/feed/', ChatFeedView.as_view(), name='chat_feed'),
    path('officer/treasurer/', TreasurerDashboardView.as_view(), name='treasurer_dashboard'),
    path('treasurer/society-fee/',SocietyFeeView.as_view(),name='treasurer_society_fee'),
    path('treasurer/society-fee/',SocietyFeeView.as_view(),name='treasurer_society_fee_create'),
    path('treasurer/society-fee-preview/', SocietyFeePreviewView.as_view(), name='society_fee_preview'),
    path('product-list', ProductListView.as_view(), name='product_list'),
    path('reports/', ReportListView.as_view(), name='reports'),
    path('treasurer/reports/create/', CreateFinancialReportView.as_view(), name='treasurer_create_report'),
    path('reports/<int:pk>/', ReportDetailView.as_view(), name='report_detail'),
    path('reports/<int:pk>/approve/', ApproveReportView.as_view(), name='report_approve'),
    path('reports/<int:pk>/blockchain/', RecordBlockchainView.as_view(), name='record_blockchain'),
    path('officer/auditor/', AuditorDashboardView.as_view(), name='auditor_dashboard'),
    path('print/', GenerateFinancialStatementView.as_view(), name='generate_fs'),
    path('print/data/', FinancialStatementDataView.as_view(), name='financial_statement_data'),
    path('print/preview/', PrintableFinancialStatementView.as_view(), name='financial_statement_print'),
    path('blockchain/financial-records/',BlockchainFinancialRecordsView.as_view(),name="financial_records"),
    path('officer/president/', PresidentDashboardView.as_view(), name='president_dashboard'),
    path('product-create', ProductCreateView.as_view(), name='product_create'),
    path('product-preview/', ProductPreviewView.as_view(), name='product_preview'),
    path('adviser/', AdviserDashboardView.as_view(), name='adviser_dashboard'),
    path('campus-admin/', CampusAdminDashboardView.as_view(), name='campus_admin_dashboard'),
    path('campus-admin/user-role/', CampusAdminUserRolesView.as_view(), name='campus_admin_user_role'),
    path("campus-admin/create-head/", CreateHeadView.as_view(), name="campus_admin_create_head"),
    path('organizations/', OrganizationListView.as_view(), name='organizations'),
    path('organizations/details/<int:pk>/', OrganizationDetailView.as_view(), name='organization_detail'),
    path("organizations/<int:pk>/", OrgPublicProfileView.as_view(), name="org_public_profile"),
    path('head/organizations/create/', CreateOrganizationView.as_view(), name='head_create_organization'),
    path('head/organizations/<int:pk>/update/', UpdateOrganizationView.as_view(), name='head_update_organization'),
    path('head/organizations/<int:pk>/delete/', DeleteOrganizationView.as_view(), name='head_delete_organization'),
    path("head/", HeadDashBoardView.as_view(), name="head_dashboard"),
    path("head/user-role", HeadUserRoleView.as_view(), name="head_user_role"),
    path('head/create-adviser', CreateAdviserView.as_view(), name='head_create_adviser'),
    path('head/create-officer', CreateOfficerView.as_view(), name='head_create_officer'),
    path('head/update-adviser/<int:pk>/', UpdateAdviserView.as_view(), name='head_update_adviser'),
    path('superadmin/', SuperAdminView.as_view(), name='superadmin_dashboard'),
    path('superadmin/user-role', UserRolesView.as_view(), name='superadmin_user_role'),
    path('superadmin/create-campus-admin', CreateCampusAdminView.as_view(), name='superadmin_create_campus_admin'),
    path('', LandingPage.as_view(), name='landing_page'),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
