from django.shortcuts import render, redirect
from django.urls import reverse_lazy, reverse
from django.views.generic import TemplateView, ListView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from accounts.models import CustomUser
from .forms import *

class HomeTemplateView(TemplateView):
    template_name = 'app/home.html'
    def dispatch(self, request, *args, **kwargs):
        user = request.user
        if user.is_authenticated:
            if user.is_superuser:
                return redirect(reverse_lazy('superadmin_dashboard'))
            elif user.role == 'treasurer':
                return redirect(reverse_lazy('treasurer_dashboard'))
            elif user.role == 'auditor':
                return redirect(reverse_lazy('auditor_dashboard'))
            elif user.role == 'adviser':
                return redirect(reverse_lazy('adviser_dashboard'))
            elif user.role == 'campus_admin':
                return redirect(reverse_lazy('campus_admin_dashboard'))
            elif user.role == 'student':
                return redirect(reverse_lazy('student_dashboard'))
        return redirect(reverse_lazy('login'))
    
class RoleRequireMixin(LoginRequiredMixin):
    role_required = None 
    login_url = '/login/'
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if self.role_required and request.user.role != self.role_required:
            raise PermissionDenied 
        return super().dispatch(request, *args, **kwargs)

class StudentDashboardView(RoleRequireMixin,TemplateView):
    template_name = 'app/student_dashboard.html'
    role_required = 'Student'

class TreasurerDashboardView(RoleRequireMixin, TemplateView):
    template_name = 'app/officer/treasurer/dashboard.html'
    role_required = 'treasurer'

class AuditorDashboardView(RoleRequireMixin, TemplateView):
    template_name = 'app/officer/auditor/dashboard.html'
    role_required = 'auditor'

class PresidentDashboardView(RoleRequireMixin, TemplateView):
    template_name = 'app/officer/president/dashboard.html'
    role_required = 'president'

class AdviserDashboardView(RoleRequireMixin, TemplateView):
    template_name = 'app/adviser/dashboard.html'
    role_required = 'adviser'

#Campus Admin Pages
class CampusAdminDashboardView(RoleRequireMixin, TemplateView):
    template_name = 'app/campus_admin/dashboard.html'
    role_required = 'campus_admin'

class CampusAdminUserRolesView(RoleRequireMixin, ListView):
    role_required = 'campus_admin'
    template_name = 'app/campus_admin/campus_admin_user_roles.html'
    context_object_name = 'users'
    paginate_by = 8

    def get_queryset(self):
        user_type = self.request.GET.get("type", "advisers")

        if user_type == "officers":
            roles = ["president", "treasurer", "auditor"]
        elif user_type == "advisers":
            roles = ["adviser"]
        else:
            return CustomUser.objects.none()

        return CustomUser.objects.filter(role__in=roles)

class CreateAdviserView(RoleRequireMixin, CreateView):
    role_required = 'campus_admin'
    form_class= AdviserCreationForm
    template_name = 'app/campus_admin/create_adviser.html'
    success_url = reverse_lazy('campus_admin_user_role')

class CreateOfficerView(RoleRequireMixin, CreateView):
    role_required = 'campus_admin'
    form_class= OfficerCreationForm
    template_name = 'app/campus_admin/create_officer.html'
    success_url = reverse_lazy('campus_admin_user_role')

class UpdateAdviserView(RoleRequireMixin, UpdateView):
    model = CustomUser
    form_class = UpdateAdviserForm
    context_object_name = 'adviser'
    role_required = 'campus_admin'
    template_name = 'app/campus_admin/update_adviser.html'


#Super Admin Pages
class SuperAdminView(RoleRequireMixin, TemplateView):
    role_required = 'super_admin'
    template_name = 'app/superadmin/dashboard.html'

class UserRolesView(RoleRequireMixin,ListView ):
    model = CustomUser
    template_name = 'app/superadmin/user_role.html'
    context_object_name = 'users'
    paginate_by = 8

    def get_queryset(self):
        user_type = self.request.GET.get("type")

        if user_type == "students":
            return CustomUser.objects.filter(role="student")

        return CustomUser.objects.exclude(role="student")

class CreateCampusAdminView(RoleRequireMixin,CreateView):
    role_required = 'super_admin'
    form_class = CampusAdminCreationForm
    template_name = 'app/superadmin/create_campus_admin.html'
    success_url = reverse_lazy('superadmin_user_role')

