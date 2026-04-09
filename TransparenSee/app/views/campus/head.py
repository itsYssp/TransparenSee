from django.contrib import messages
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse_lazy, reverse
from django.views.generic import TemplateView, ListView, CreateView, UpdateView, DeleteView, DetailView
from accounts.models import CustomUser
from ...forms import *
from ..mixins import *
class HeadDashBoardView(RoleRequireMixin, TemplateView):
    template_name = 'app/heads/dashboard.html'
    role_required = 'head'
    
    def get_organization(self):
        return self.request.user.officer.organization

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["latest_ay"] = AcademicYear.objects.order_by("-academic_year", "-semester").first()
        context["total_organizations"] = Organization.objects.count()
        context["total_users"] = CustomUser.objects.count()
        return context
    
    def post(self, request, *args, **kwargs):
        action = request.POST.get('action')

        if action == 'add_academic_year':
            academic_year = request.POST.get('academic_year_input')
            semester = request.POST.get('semester_input')

            if not academic_year or not semester:
                messages.error(request, "Academic Year and Semester required.")
                return redirect('head_dashboard')

            ay, _ = AcademicYear.objects.get_or_create(
                academic_year=academic_year,
                semester=semester
            )


            organizations = Organization.objects.all()  

            new_fees = []

            for org in organizations:
                students = CustomUser.objects.filter(
                    role='student',
                    student__organization=org
                )
                society_fee_amount = org.society_fee_amount or 0

                existing = SocietyFee.objects.filter(
                    academic_year=ay,
                    organization=org
                ).values_list('student_id', flat=True)

                for s in students:
                    if s.pk not in existing:
                        new_fees.append(
                            SocietyFee(
                                organization=org,
                                student=s,
                                academic_year=ay,
                                semester = semester,
                                amount=society_fee_amount,
                                amount_paid=0,
                                status='unpaid'
                            )
                        )

            SocietyFee.objects.bulk_create(new_fees)

            messages.success(
                request,
                f'{len(new_fees)} records created for all organizations.'
            )

            return redirect('head_dashboard')

class HeadUserRoleView(RoleRequireMixin, ListView):
    template_name = 'app/heads/heads_user_role.html'
    role_required = 'head'
    context_object_name = 'users'
    paginate_by = 8

    def get_queryset(self):
        user_type = self.request.GET.get("type", "advisers")

        if user_type == "officers":
            roles = ["president", "treasurer", "auditor"]
        elif user_type == "advisers":
            roles = ["adviser", "co_adviser"]
        else:
            return CustomUser.objects.none()

        return CustomUser.objects.filter(role__in=roles).order_by('date_joined')
    
class CreateOrganizationView(RoleRequireMixin, CreateView):
    model = Organization
    template_name = 'app/heads/create_organization.html'
    role_required = 'head'
    form_class = OrganizationForm
    success_url = reverse_lazy('organizations')

    def form_valid(self, form):
       messages.success(self.request, f'Organization "{form.instance.name}" created successfully.')
       return super().form_valid(form)


class UpdateOrganizationView(RoleRequireMixin, UpdateView):
    model = Organization
    template_name = 'app/heads/update_organization.html'
    role_required = 'head'
    form_class = OrganizationForm
    context_object_name = 'org'
    success_url = reverse_lazy('organizations')


    def form_valid(self, form):
        messages.success(self.request, f'Organization "{form.instance.name}" updated successfully.')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Please fix the errors below.')
        return super().form_invalid(form)


class DeleteOrganizationView(RoleRequireMixin, DeleteView):
    model = Organization
    role_required = 'head'
    success_url = reverse_lazy('organizations')

    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)

    def form_valid(self, form):
        name = self.get_object().name
        messages.success(self.request, f'Organization "{name}" deleted successfully.')
        return super().form_valid(form)

class CreateAdviserView(RoleRequireMixin, CreateView):
    role_required = 'head'
    form_class= AdviserCreationForm
    template_name = 'app/heads/create_adviser.html'
    success_url = reverse_lazy('head_user_role')

class CreateOfficerView(RoleRequireMixin, CreateView):
    role_required = 'head'
    form_class= OfficerCreationForm
    template_name = 'app/heads/create_officer.html'
    success_url = reverse_lazy('head_user_role')

class UpdateAdviserView(RoleRequireMixin, UpdateView):
    model = Adviser
    context_object_name = 'adviser'
    fields = ['employee_id', 'department', 'organization']
    role_required = 'head'
    template_name = 'app/heads/update_adviser.html'

    def get_object(self):
        return get_object_or_404(Adviser, user__pk=self.kwargs['pk'])
    
    def form_valid(self, form):
        adviser = form.save()
        user = adviser.user
        user.first_name = self.request.POST.get('first_name', user.first_name)
        user.last_name = self.request.POST.get('last_name', user.last_name)
        user.username = self.request.POST.get('username', user.username)
        user.email = self.request.POST.get('email', user.email)
        user.save()
        
        return render(self.request, self.template_name, {
            'form': form,
            'adviser': adviser,
            'show_modal': True,
            'modal_type': 'success',
            'modal_message': 'Adviser updated successfully.',
        })

    def get_success_url(self):
        return reverse('campus_admin_user_role')