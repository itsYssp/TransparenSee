from django.contrib import messages
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse_lazy, reverse
from django.views.generic import TemplateView, ListView, CreateView, UpdateView, DeleteView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from accounts.models import CustomUser
from .forms import *
from .blockchain import contract_abi
from datetime import datetime
from web3 import Web3
from django.core.paginator import Paginator
from web3.middleware.geth_poa import geth_poa_middleware
from django.contrib.auth import update_session_auth_hash
import os
from dotenv import load_dotenv
from .models import SocietyFee, Organization
from django.db.models import Case, Count, When, IntegerField
from django.db.models.functions import Substr, Cast
from django.db.models import Q
from decimal import Decimal


class HomeTemplateView(TemplateView):
    template_name = 'app/home.html'
    def dispatch(self, request, *args, **kwargs):
        user = request.user
        if user.is_authenticated:
            if user.is_superuser:
                return redirect(reverse_lazy('superadmin_dashboard'))
            elif user.role == 'treasurer':
                return redirect(reverse_lazy('treasurer_dashboard'))
            elif user.role == 'auditor':
                return redirect(reverse_lazy('auditor_dashboard'))
            elif user.role == 'adviser':
                return redirect(reverse_lazy('adviser_dashboard'))
            elif user.role == 'president':
                return redirect(reverse_lazy('president_dashboard'))
            elif user.role == 'campus_admin':
                return redirect(reverse_lazy('campus_admin_dashboard'))
            elif user.role == 'head':
                return redirect(reverse_lazy('head_dashboard'))
            elif user.role == 'student':
                return redirect(reverse_lazy('student_dashboard'))
        return redirect(reverse_lazy('login'))
        

class LandingPage(TemplateView):
    template_name = 'app/landing_page.html'
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(reverse_lazy('home'))
        return super().dispatch(request, *args, **kwargs)
    
class RoleRequireMixin(LoginRequiredMixin):
    role_required = None 
    login_url = '/login/'
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if self.role_required and request.user.role not in self.role_required:
            raise PermissionDenied

        return super().dispatch(request, *args, **kwargs)
    
#------ TREASURER --------
class TreasurerDashboardView(RoleRequireMixin, TemplateView):
    template_name = 'app/officer/treasurer/dashboard.html'
    role_required = 'treasurer'

class SocietyFeeView(RoleRequireMixin, TemplateView):
    template_name = 'app/officer/treasurer/society_fee.html'
    role_required = 'treasurer'

    def get_organization(self):
        return self.request.user.officer.organization

    def get(self, request, *args, **kwargs):
        org = self.get_organization()
        

        fees = SocietyFee.objects.filter(
            organization=org
        ).select_related(
            'student', 'student__student', 'academic_year'
        ).order_by('-created_at')

        search = request.GET.get('search', '').strip()
        academic_year = request.GET.get('academic_year', '')
        semester = request.GET.get('semester', '')
        semester_choices = SocietyFee.SEMESTER_CHOICES 

        if search:
            fees = fees.filter(
                Q(student__first_name__icontains=search) |
                Q(student__last_name__icontains=search) |
                Q(student__student__student_id__icontains=search)
            ).distinct()

        if academic_year:
            fees = fees.filter(academic_year__id=academic_year)

        if semester:
            fees = fees.filter(semester=semester)

        total_students = fees.count()
        paid_count = fees.filter(status='paid').count()
        unpaid_count = fees.filter(status='unpaid').count()

        paid_percent = round((paid_count / total_students) * 100) if total_students else 0
        unpaid_percent = round((unpaid_count / total_students) * 100) if total_students else 0

        paginator = Paginator(fees, 8)
        page_obj = paginator.get_page(request.GET.get('page'))

        academic_years = AcademicYear.objects.order_by('-academic_year')

        students = CustomUser.objects.filter(
            role='student',
            student__organization=org
        ).select_related('student').order_by('first_name')

        return render(request, self.template_name, {
            'society_fees': page_obj,
            'page_obj': page_obj,
            'students': students,
            'semester': semester_choices,
            'academic_years': academic_years,
            'total_students': total_students,
            'paid_count': paid_count,
            'unpaid_count': unpaid_count,
            'paid_percent': paid_percent,
            'unpaid_percent': unpaid_percent,
        })

    def post(self, request, *args, **kwargs):
        action = request.POST.get('action')
        org = self.get_organization()
        

        if action == 'delete':
            fee = get_object_or_404(SocietyFee, pk=request.POST.get('fee_id'), organization=org)
            fee.delete()
            messages.success(request, 'Deleted successfully.')
            return redirect('treasurer_society_fee')

        if action == 'update':
            fee = get_object_or_404(SocietyFee, pk=request.POST.get('fee_id'), organization=org)
            fee.amount = request.POST.get('amount')
            fee.amount_paid = request.POST.get('amount_paid')
            fee.status = request.POST.get('status')
            fee.academic_year_id = request.POST.get('academic_year')
            fee.save()
            messages.success(request, 'Updated successfully.')
            return redirect('treasurer_society_fee')

        # CREATE
        academic_year_id = request.POST.get('academic_year')
        student_id = request.POST.get('student')
        semester = request.POST.get('semester')

        ay = get_object_or_404(AcademicYear, pk=academic_year_id)
        student = get_object_or_404(CustomUser, pk=student_id)

        if SocietyFee.objects.filter(
            student=student,
            organization=org,
            academic_year=ay,
            semester=semester
        ).exists():
            messages.error(request, 'Record already exists.')
            return redirect('treasurer_society_fee')

        SocietyFee.objects.create(
            organization=org,
            student=student,
            academic_year=ay,
            semester=semester,
            amount=request.POST.get('amount', 0),
            amount_paid=request.POST.get('amount_paid', 0),
            status=request.POST.get('status', 'unpaid'),
        )

        messages.success(request, 'Added successfully.')
        return redirect('treasurer_society_fee')


class AuditorDashboardView(RoleRequireMixin, TemplateView):
    template_name = 'app/officer/auditor/dashboard.html'
    role_required = 'auditor'

class PresidentDashboardView(RoleRequireMixin, TemplateView):
    template_name = 'app/officer/president/dashboard.html'
    role_required = 'president'

    def get_organization(self, user):
        return user.officer.organization 

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        org = self.get_organization(user)
        
        context["society_fee_amount"] = org.society_fee_amount
        return context
    

    def post(self, request, *args, **kwargs):
        action = request.POST.get('action')
        org = self.get_organization(request.user) 

        if action == 'update_fee_amount':
            amount = request.POST.get('update_fee_input')

            try:
                org.society_fee_amount = float(amount)
                org.save()
                messages.success(request, "Society fee updated successfully.")
            except:
                messages.error(request, "Invalid amount.")

        return redirect('president_dashboard')
    

class AdviserDashboardView(RoleRequireMixin, TemplateView):
    template_name = 'app/adviser/dashboard.html'
    role_required = 'adviser'

#Campus Admin Pages
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
            officer_count=Count('officer'),
            adviser_count=Count('adviser')
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
        user_type = self.request.GET.get("type", "adviser")

        if user_type == "officers":
            roles = ["president", "treasurer", "auditor"]
        elif user_type == "advisers":
            roles = ["adviser"]
        else:
            return CustomUser.objects.none()

        return CustomUser.objects.filter(role__in=roles).order_by('date_joined')
    
class CreateOrganizationView(RoleRequireMixin, CreateView):
    model = Organization
    template_name = 'app/heads/create_organization.html'
    role_required = 'head'
    form_class = OrganizationForm
    success_url = reverse_lazy('organizations')

    ## def form_valid(self, form):
       ##  messages.success(self.request, f'Organization "{form.instance.name}" created successfully.')
       ##  return super().form_valid(form)


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
    template_name = 'app/campus_admin/update_adviser.html'

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

#Super Admin Pages
class SuperAdminView(RoleRequireMixin, TemplateView):
    role_required = 'super_admin'
    template_name = 'app/superadmin/dashboard.html'

class UserRolesView(RoleRequireMixin,ListView ):
    model = CustomUser
    template_name = 'app/superadmin/user_role.html'
    context_object_name = 'users'
    paginate_by = 8

    def get_queryset(self):
        user_type = self.request.GET.get("type")

        if user_type == "student":
            roles = ["student"]
        elif user_type == "adviser":
            roles = ["adviser"]
        else:
            roles = ["campus_admin", "super_admin"]
        return CustomUser.objects.filter(role__in=roles).order_by('date_joined')

class CreateCampusAdminView(RoleRequireMixin,CreateView):
    role_required = 'super_admin'
    form_class = CampusAdminCreationForm
    template_name = 'app/superadmin/create_campus_admin.html'
    success_url = reverse_lazy('superadmin_user_role')

class StudentDashboardView(RoleRequireMixin, ListView):
    template_name = 'app/student/dashboard.html'
    model= CustomUser
    role_required = 'student'
    paginate_by = 8
    context_object_name = 'users'

    
# ------- STUDENT ----------
class StudentView(RoleRequireMixin,TemplateView):
    template_name = "app/student/student_dashboard.html"
    role_required = 'student'

    load_dotenv()
    SEPOLIA_URL = os.getenv("SEPOLIA_URL")
    CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS")
    web3 = Web3(Web3.HTTPProvider(SEPOLIA_URL))
    web3.middleware_onion.inject(geth_poa_middleware, layer=0)
    contract = web3.eth.contract(address=CONTRACT_ADDRESS, abi=contract_abi)

    def get_context_data(self, **kwargs):
        
        context = super().get_context_data(**kwargs)

        # Fetch transactions from blockchain
        try:
            transactions = self.contract.functions.getTransactions().call()
        except Exception as e:
            transactions = []
            print("Error fetching transactions:", e)

        tx_list = []
        for t in transactions:
            tx_list.append({
                "organization": t[0],
                "amount": t[1],
                "sender": t[2],
                "timestamp": datetime.fromtimestamp(t[3]).strftime('%Y-%m-%d %H:%M:%S')
            })

        context['transactions'] = tx_list
        context['tx_count'] = len(tx_list)
        return context


class StudentProfileView(RoleRequireMixin, TemplateView):
    template_name = 'app/student/student_profile.html'
    role_required = 'student'

    def post(self, request, *args, **kwargs):
        action = request.POST.get('action')

        if action == 'change_password':
            old_password = request.POST.get('old_password', '').strip()
            new_password1 = request.POST.get('new_password1', '').strip()
            new_password2 = request.POST.get('new_password2', '').strip()

            if not old_password:
                messages.error(request, 'Current password is required.')
            elif not new_password1:
                messages.error(request, 'New password is required.')
            elif not new_password2:
                messages.error(request, 'Please confirm your new password.')
            elif not request.user.check_password(old_password):
                messages.error(request, 'Current password is incorrect.')
            elif new_password1 != new_password2:
                messages.error(request, 'New passwords do not match.')
            elif len(new_password1) < 8:
                messages.error(request, 'Password must be at least 8 characters.')
            else:
                request.user.set_password(new_password1)
                request.user.save()
                update_session_auth_hash(request, request.user)
                messages.success(request, 'Password changed successfully.')
            return redirect(request.path)

        student, _ = Student.objects.get_or_create(user=request.user)
        form = StudentForm(request.POST, request.FILES, instance=student)

        if form.is_valid():
            form.save()
            user = request.user
            user.profile_image = request.POST.get('profile_image', user.profile_image)
            user.first_name = request.POST.get('first_name', user.first_name)
            user.last_name = request.POST.get('last_name', user.last_name)
            user.username = request.POST.get('username', user.username)
            user.email = request.POST.get('email', user.email)
            if 'profile_image' in request.FILES:
                user.profile_image = request.FILES['profile_image']
            user.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect(request.path)

        return self.render_to_response(self.get_context_data(form=form))
    
class ChatView(RoleRequireMixin, TemplateView):
    template_name = 'app/officer/officer_chat.html'
    role_required = ["treasurer", "auditor", "president", "adviser", "campus_admin"]

    def get_organization(self, user):
        if hasattr(user, 'officer'):
            return user.officer.organization
        elif hasattr(user, 'adviser'):
            return user.adviser.organization
        elif hasattr(user, 'campus_admin'):
            return getattr(user.campus_admin, 'organization', None)
        return None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        org = self.get_organization(user)

        context["global_messages"] = GlobalChat.objects.select_related(
            "user"
        ).order_by("createdAt")[:50]

        if org:
            context["announcements"] = OrganizationAnnouncement.objects.filter(
                organization=org
            ).select_related("author").order_by("-createdAt")
        else:
            context["announcements"] = OrganizationAnnouncement.objects.none()

        role_templates = {
            "treasurer": "app/officer/treasurer/sidebar.html",
            "auditor": "app/officer/auditor/sidebar.html",
            "president": "app/officer/president/sidebar.html",
            "adviser": "app/adviser/sidebar.html",
            "campus_admin": "app/campus_admin/sidebar.html",
        }
        context["base_template"] = role_templates.get(user.role, "app/base.html")
        context["chat_form"] = GlobalChatForm()
        context["announcement_form"] = AnnouncementForm()
        return context

    def post(self, request, *args, **kwargs):
        tab = request.POST.get("type", "global_chat")
        user = request.user
        org = self.get_organization(user)

        
        if tab == "global_chat":
            form = GlobalChatForm(request.POST)
            if form.is_valid():
                chat = form.save(commit=False)
                chat.user = user
                chat.save()
            else:
                print(form.errors)

        elif tab == "organization_announcement":
            form = AnnouncementForm(request.POST)
            if form.is_valid():
                ann = form.save(commit=False)
                ann.author = user
                ann.organization = org
                ann.save()
            else:
                print(form.errors)

        return redirect(f"{request.path}?type={tab}")