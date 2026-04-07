from django.views.generic import TemplateView
from ...models import *
from ..mixins import *
from django.db.models import Q, Count


class AuditorDashboardView(RoleRequireMixin, TemplateView):
    template_name = 'app/officer/auditor/dashboard.html'
    role_required = 'auditor'

    def get_organization(self):
        return self.request.user.officer.organization

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        org = self.get_organization()
        recent_approval_logs = ReportApprovalLog.objects.filter(report__organization = org).order_by('-created_at')[:3]
        context["pending_financial_reports"] = FinancialReport.objects.filter(organization=org).exclude(status='rejected').count()
        context["approved_financial_reports"] = FinancialReport.objects.filter(organization=org, status='approved').count()
        context["flagged_financial_reports"] = FinancialReport.objects.filter(organization=org, status='rejected').count()
        context['recent_financial_reports'] = FinancialReport.objects.filter(organization=org).exclude(status='rejected').annotate(
            income_count=Count('entries', filter=Q(entries__entry_type='income')),
            expense_count=Count('entries', filter=Q(entries__entry_type='expense')),
        ).order_by('-created_at')[:3]
        context["society_fee_amount"] = org.society_fee_amount
        context["recent_approval_logs"] = recent_approval_logs
        return context
    