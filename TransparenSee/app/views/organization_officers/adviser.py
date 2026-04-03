from django.views.generic import TemplateView
from ..mixins import *

class AdviserDashboardView(RoleRequireMixin, TemplateView):
    template_name = 'app/adviser/dashboard.html'
    role_required = 'adviser'
