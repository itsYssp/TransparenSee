from django.views.generic import ListView
from django.shortcuts import redirect
from django.contrib import messages
from ... models import *
from ...forms import AccomplishmentReportForm
from ..mixins import RoleRequireMixin

class SecretaryHomepageView(RoleRequireMixin, ListView):
    template_name = 'app/officer/secretary/homepage.html'
    role_required = 'secretary'
    model = AccomplismentReport
    context_object_name = 'accomplishment_report'

    def get_queryset(self):
        organization = getattr(self.request.user.officer, 'organization', None)
        if organization is None:
            return AccomplismentReport.objects.none()
        return AccomplismentReport.objects.filter(organization=organization)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = kwargs.get('form') or AccomplishmentReportForm()
        return context

    def post(self, request, *args, **kwargs):
        form = AccomplishmentReportForm(request.POST, request.FILES)
        organization = getattr(request.user.officer, 'organization', None)

        if organization is None:
            messages.error(request, 'No organization is assigned to this secretary account.')
            self.object_list = self.get_queryset()
            return self.render_to_response(self.get_context_data(form=form))

        if form.is_valid():
            report = form.save(commit=False)
            report.organization = organization
            report.created_by = request.user
            report.save()
            messages.success(request, 'Accomplishment report uploaded successfully.')
            return redirect('secretary_homepage')

        messages.error(request, 'Please fix the form errors before submitting.')
        self.object_list = self.get_queryset()
        return self.render_to_response(self.get_context_data(form=form))
