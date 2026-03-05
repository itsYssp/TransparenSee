from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import TemplateView, ListView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from accounts.models import CustomUser
from .forms import CampusAdminCreationForm

class HomeTemplateView(TemplateView):
    template_name = 'app/home.html'

class RoleRequireMixin(LoginRequiredMixin):
    role_required = None 
    login_url = '/login/'
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if self.role_required and request.user.role != self.role_required:
            raise PermissionDenied 
        return super().dispatch(request, *args, **kwargs)

class StudentDashboardTemplate(RoleRequireMixin,TemplateView):
    template_name = 'app/student_dashboard.html'
    role_required = 'Student'

class TreasurerDashboardTemplate(RoleRequireMixin, TemplateView):
    template_name = 'app/officer/treasurer/dashboard.html'
    role_required = 'treasurer'

class AuditorDashboardTemplate(RoleRequireMixin, TemplateView):
    template_name = 'app/officer/auditor/dashboard.html'
    role_required = 'auditor'

class PresidentDashboardTemplate(RoleRequireMixin, TemplateView):
    template_name = 'app/officer/president/dashboard.html'
    role_required = 'president'

class CampusAdminDashboardTemplate(RoleRequireMixin, TemplateView):
    template_name = 'app/campus_admin/dashboard.html'
    role_required = 'campus_admin'

class AdviserDashboardTemplate(RoleRequireMixin, TemplateView):
    template_name = 'app/adviser/dashboard.html'
    role_required = 'adviser'

#Super Admin Pages
class SuperAdminTemplate(RoleRequireMixin, TemplateView):
    role_required = 'super_admin'
    template_name = 'app/superadmin/dashboard.html'

class UserRolseTemplate(RoleRequireMixin,ListView ):
    model = CustomUser
    template_name = 'app/superadmin/user_role.html'
    context_object_name = 'users'
    paginate_by = 8

    def get_queryset(self):
        user_type = self.request.GET.get("type")

        if user_type == "students":
            return CustomUser.objects.filter(role="student")

        return CustomUser.objects.exclude(role="student")

class CreateCampusAdminTemplate(CreateView):
    form_class = CampusAdminCreationForm
    template_name = 'app/superadmin/create_campus_admin.html'
    success_url = reverse_lazy('superadmin_user_role')
