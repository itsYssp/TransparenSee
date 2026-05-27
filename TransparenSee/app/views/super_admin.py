from django.contrib import messages
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse_lazy, reverse
from django.views.generic import TemplateView, ListView, CreateView, UpdateView, DeleteView, DetailView
from accounts.models import CustomUser
from ..forms import *
from ..models import *
from .mixins import *
from django.db.models  import Sum

class SuperAdminView(RoleRequireMixin, TemplateView):
    role_required = 'admin'
    template_name = 'app/superadmin/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["total_user"] = CustomUser.objects.count()
        context['total_org'] = Organization.objects.count()
        context['total_on_blockchain'] = FinancialReport.objects.filter(status='on_blockchain').count()
        context['recent_approval_logs'] = ReportApprovalLog.objects.all()[:10]
        context['org_balance'] = Organization.objects.aggregate(
            total_balance=Sum('balance')
        )
        return context
    

class UserRolesView(RoleRequireMixin,ListView ):
    model = CustomUser
    template_name = 'app/superadmin/user_role.html'
    context_object_name = 'users'
    paginate_by = 8
    role_required = 'admin'

    def get_queryset(self):
        user_type = self.request.GET.get("type")

        if user_type == "student":
            roles = ["student"]
        elif user_type == "adviser":
            roles = ["adviser"]
        else:
            roles = ["campus_admin", "super_admin", "head"]
        return CustomUser.objects.filter(role__in=roles).order_by('date_joined')

class CreateCampusAdminView(RoleRequireMixin,CreateView):
    role_required = 'admin'
    form_class = CampusAdminCreationForm
    template_name = 'app/superadmin/create_campus_admin.html'
    success_url = reverse_lazy('superadmin_user_role')