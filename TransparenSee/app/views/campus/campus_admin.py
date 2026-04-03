from django.urls import reverse_lazy

from accounts.models import CustomUser
from ..mixins import *
from django.views.generic import CreateView, ListView, TemplateView
from ...models import *
from ...forms import *

class CampusAdminDashboardView(RoleRequireMixin, TemplateView):
    template_name = 'app/campus_admin/dashboard.html'
    role_required = 'campus_admin'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["total_organizations"] = Organization.objects.count()
        context["total_users"] = CustomUser.objects.count()
        return context
    

class CampusAdminUserRolesView(RoleRequireMixin, ListView):
    role_required = 'campus_admin'
    template_name = 'app/campus_admin/campus_admin_user_roles.html'
    context_object_name = 'users'
    paginate_by = 8

    def get_queryset(self):
        user_type = self.request.GET.get("type", "heads")

        if user_type == "officers":
            roles = ["president", "treasurer", "auditor"]
        elif user_type == "advisers":
            roles = ["adviser"]
        elif user_type == "heads":
            roles = ["head"]
        else:
            return CustomUser.objects.none()

        return CustomUser.objects.filter(role__in=roles).order_by('date_joined')

class CreateHeadView(RoleRequireMixin, CreateView):
    role_required = 'campus_admin'
    form_class= HeadCreationForm
    template_name = 'app/campus_admin/create_head.html'
    success_url = reverse_lazy('campus_admin_user_role')
