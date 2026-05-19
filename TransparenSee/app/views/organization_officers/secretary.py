from django.views.generic import ListView
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from ... models import *
from ...forms import AccomplishmentReportForm
from ..mixins import RoleRequireMixin

class SecretaryHomepageView(RoleRequireMixin, ListView):
    template_name = 'app/officer/secretary/homepage.html'
    role_required = 'secretary'
    model = AccomplishmentReport

    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        org = self.request.user.officer.organization
        context['form'] = kwargs.get('form') or AccomplishmentReportForm()
        context['accomplishment_report'] = AccomplishmentReport.objects.filter(organization=org)
        return context

    def post(self, request, *args, **kwargs):
        organization = getattr(request.user.officer, 'organization', None)

        if organization is None:
            messages.error(request, 'No organization is assigned to this secretary account.')
            return redirect('secretary_homepage')

        # Handle delete
        if request.POST.get('action') == 'delete':
            report_id = request.POST.get('report_id')
            report = get_object_or_404(AccomplishmentReport, pk=report_id, organization=organization)
            report.delete()
            messages.success(request, 'Accomplishment report deleted successfully.')
            return redirect('secretary_homepage')
        # Handle upload
        form = AccomplishmentReportForm(request.POST, request.FILES)
        if form.is_valid():
            report = form.save(commit=False)
            report.organization = organization
            report.created_by = request.user
            report.save()

            AccomplishmentReportLog.objects.create(
                report=report,
                action_by=request.user,
                action='submitted',
            )

            messages.success(request, 'Accomplishment report uploaded successfully.')
            return redirect('secretary_homepage')

        messages.error(request, 'Please fix the form errors before submitting.')
        return redirect('secretary_homepage')
