from ..mixins import *
from django.views.generic import TemplateView, ListView, DetailView
from ...models import *
from django.db.models import Count

class OrganizationListView(RoleRequireMixin, ListView):
    model = Organization
    template_name = 'app/organizations.html'
    context_object_name = 'organizations'
    role_required = ['campus_admin', 'head']
    paginate_by = 10

    def get_queryset(self):
        queryset = Organization.objects.all().order_by('name')
        search = self.request.GET.get('search', '').strip()
        if search:
            queryset = queryset.filter(name__icontains=search)
        return queryset

    def get_context_data(self,**kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        role_template = {
            "head": "app/heads/sidebar.html",
            "campus_admin ": "app/campus_admin/sidebar.html", 
        }

        context["base_template"] = role_template.get(user.role,  'app/base.html')
        context['total_organizations'] = Organization.objects.count()
        context['search'] = self.request.GET.get('search', '')
        organizations = Organization.objects.annotate(
            officer_count=Count('officer',distinct=True),
            adviser_count=Count('adviser',distinct=True)
        )
        context['organizations'] = organizations
        return context


class OrganizationDetailView(RoleRequireMixin, DetailView):
    model = Organization
    template_name = 'app/organization_detail.html'
    context_object_name = 'org'
    role_required = ['campus_admin', 'head']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        org = self.get_object()
        user = self.request.user



        role_template = {
            "head": "app/heads/sidebar.html",
            "campus_admin ": "app/campus_admin/sidebar.html", 
        }

        context["base_template"] = role_template.get(user.role,  'app/base.html')

        # Officers in this org
        context['officers'] = Officer.objects.filter(
            organization=org
        ).select_related('user').order_by('user__first_name')

        # Advisers in this org
        context['advisers'] = Adviser.objects.filter(
            organization=org
        ).select_related('user').order_by('user__first_name')

        # Society fees
        context['society_fees'] = SocietyFee.objects.filter(
            organization=org
        ).order_by('-created_at')

        context['org_category'] = org.category

        # Stats
        context['total_officers'] = context['officers'].count()
        context['total_advisers'] = context['advisers'].count()
        context['paid_fees'] = SocietyFee.objects.filter(
            organization=org, status='paid'
        ).count()
        context['unpaid_fees'] = SocietyFee.objects.filter(
            organization=org, status='unpaid'
        ).count()

        return context