from django.urls import reverse_lazy
from django.shortcuts import render, get_object_or_404, redirect
from accounts.models import CustomUser
from ..mixins import *
from django.views.generic import CreateView, ListView, TemplateView, UpdateView
from ...models import *
from ...forms import *
from django.db.models import Sum, Count, Q

class CampusAdminDashboardView(RoleRequireMixin, TemplateView):
    template_name = 'app/campus_admin/dashboard.html'
    role_required = 'campus_admin'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["total_organizations"] = Organization.objects.count()
        context["total_users"] = CustomUser.objects.count()
        context['org_balance'] = Organization.objects.aggregate(
            total_balance=Sum('balance')
        )
        context['verified_financial_report_count'] = FinancialReport.objects.filter(status='on_blockchain').count()
        context['pending_financial_report_count'] = FinancialReport.objects.exclude(status__in=['rejected',"on_blockchain"]).count()
        context['recent_financial_reports'] = FinancialReport.objects.exclude(status='rejected').annotate(
            income_count=Count('entries', filter=Q(entries__entry_type='income')),
            expense_count=Count('entries', filter=Q(entries__entry_type='expense')),
        ).order_by('-created_at')[:4]
        context['recent_approval_logs'] = ReportApprovalLog.objects.order_by('-created_at')[:5]
        context['accomplishment_report'] = AccomplishmentReport.objects.all()[:3]
        context['accomplishment_report_count'] = AccomplishmentReport.objects.all().count()

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
            roles = ["adviser", 'co_adviser']
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

class UpdateHeadView(RoleRequireMixin, UpdateView):
    model = Head
    context_object_name = 'head'
    fields = ['employee_id', 'department', 'campus']
    role_required = 'campus_admin'
    template_name = 'app/campus_admin/update_head.html'

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