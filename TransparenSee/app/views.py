from django.shortcuts import render
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied

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

class OfficerDashboardTemplate(RoleRequireMixin,TemplateView):
    template_name = 'app/officer/dashboard.html'
    role_required = 'officer'

class StudentDashboardTemplate(RoleRequireMixin,TemplateView):
    template_name = 'app/student_dashboard.html'
    role_required = 'student'