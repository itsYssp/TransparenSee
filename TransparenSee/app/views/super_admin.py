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
    

class UserRolesView(RoleRequireMixin, ListView):
    model = CustomUser
    template_name = 'app/superadmin/user_role.html'
    context_object_name = 'users'
    paginate_by = 15
    role_required = 'admin'

    def get_queryset(self):
        user_type = self.request.GET.get("type")

        if user_type == "student":
            roles = ["student"]
        elif user_type == "adviser":
            roles = ["adviser"]
        else:
            roles = ["campus_admin", "super_admin", "head"]
        return CustomUser.objects.filter(role__in=roles).order_by('-date_joined', '-pk')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        page_obj = ctx["page_obj"]
        ctx["page_range"] = page_obj.paginator.get_elided_page_range(
            page_obj.number, on_each_side=1, on_ends=1
        )
        ctx["user_type"] = self.request.GET.get("type", "system")
        return ctx

class CreateCampusAdminView(RoleRequireMixin,CreateView):
    role_required = 'admin'
    form_class = CampusAdminCreationForm
    template_name = 'app/superadmin/create_campus_admin.html'
    success_url = reverse_lazy('superadmin_user_role')

class AdminCreateHeadView(RoleRequireMixin, CreateView):
    role_required = 'admin'
    form_class= HeadCreationForm
    template_name = 'app/superadmin/admin_create_head.html'
    success_url = reverse_lazy('admin_user_role')

class AdminUpdateHeadView(RoleRequireMixin, UpdateView):
    model = Head
    context_object_name = 'head'
    fields = ['employee_id', 'department', 'campus']
    role_required = 'admin'
    template_name = 'app/superadmin/admin_update_head.html'

    def get_object(self):
        return get_object_or_404(Head, user__pk=self.kwargs['pk'])
    
    def form_valid(self, form):
        head = form.save()
        user = head.user
        user.first_name = self.request.POST.get('first_name', user.first_name)
        user.last_name = self.request.POST.get('last_name', user.last_name)
        user.middle_name = self.request.POST.get('middle_name', user.middle_name)
        user.username = self.request.POST.get('username', user.username)
        user.email = self.request.POST.get('email', user.email)
        user.save()
        
        return render(self.request, self.template_name, {
            'form': form,
            'adviser': head,
            'show_modal': True,
            'modal_type': 'success',
            'modal_message': 'Adviser updated successfully.',
        })

    def get_success_url(self):
        return reverse('head_user_role')