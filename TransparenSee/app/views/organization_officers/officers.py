from django.utils import timezone 
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import TemplateView, ListView, CreateView, UpdateView, DeleteView, DetailView
from ...forms import *
from ..mixins import *
from django.db.models import Sum, Q, Count 
from ...blockchain import verify_report_hash
from itertools import groupby  



class ApproveReportView(RoleRequireMixin, TemplateView):
    role_required = ['auditor', 'president', 'adviser', 'co_adviser']

    def post(self, request, pk):
        report = get_object_or_404(FinancialReport, pk=pk)
        action = request.POST.get('action')
        remarks = request.POST.get('remarks', '')
        user = request.user

        if action == 'approve':
            if user.role == 'auditor' and report.status == 'pending_auditor':
                report.auditor_approved_by = user
                report.auditor_approved_at = timezone.now()
                report.auditor_remarks = remarks
                report.status = 'pending_president'
                report.save()
                ReportApprovalLog.objects.create(
                    report=report, action_by=user,
                    action='approved', remarks=remarks
                )
                messages.success(request, 'Report approved. Sent to President.')

            elif user.role == 'president' and report.status == 'pending_president':
                report.president_approved_by = user
                report.president_approved_at = timezone.now()
                report.president_remarks = remarks
                report.status = 'pending_co_adviser'
                report.save()
                ReportApprovalLog.objects.create(
                    report=report, action_by=user,
                    action='approved', remarks=remarks
                )
                messages.success(request, 'Report approved. Sent to Co-Adviser.')

            elif user.role == 'co_adviser' and report.status == 'pending_co_adviser':
                report.co_adviser_approved_by= user
                report.co_adviser_approved_at = timezone.now()
                report.co_adviser_remarks = remarks
                report.status = 'pending_adviser'
                report.save()
                ReportApprovalLog.objects.create(
                    report=report, action_by=user,
                    action='approved', remarks=remarks
                )
                messages.success(request, 'Report approved. Sent to Adviser.')

            elif user.role == 'adviser' and report.status == 'pending_adviser':
                report.adviser_approved_by = user
                report.adviser_approved_at = timezone.now()
                report.adviser_remarks = remarks
                report.status = 'approved'
                report.save()
                
                entities = report.entries.all()
                total_income = entities.filter(entry_type='income').aggregate(t=Sum('amount'))['t'] or 0
                total_expense = entities.filter(entry_type='expense').aggregate(t=Sum('amount'))['t'] or 0
                net = total_income - total_expense

                org = report.organization
                org.balance = (org.balance or 0) + net
                org.save(update_fields=['balance'])

                ReportApprovalLog.objects.create(
                    report=report, action_by=user,
                    action='approved', remarks=remarks
                )
                messages.success(request, 'Report fully approved and ready for blockchain.')

        elif action == 'reject':
            report.status = 'rejected'
            report.save()
            ReportApprovalLog.objects.create(
                report=report, action_by=user,
                action='rejected', remarks=remarks
            )
            messages.error(request, 'Report rejected.')

        return redirect('report_detail', pk=pk)

class ReportListView(ListView):
    model = FinancialReport
    template_name = 'app/officer/treasurer/report_list.html'
    paginate_by = 10

    def get_queryset(self):
        user = self.request.user
        qs = super().get_queryset().select_related(
            'organization', 'created_by', 'academic_year'
        ).prefetch_related('entries')

       
        if hasattr(user, 'officer'):
            qs = qs.filter(organization=user.officer.organization)
        elif hasattr(user, 'adviser'):
            qs = qs.filter(organization=user.adviser.organization)
        elif hasattr(user, 'campus_admin'):
            qs = qs  


        search = self.request.GET.get('search', '').strip()
        if search:
            qs = qs.filter(title__icontains=search)


        status = self.request.GET.get('status')
        if status   :
            qs = qs.filter(status=status)

        qs = qs.annotate(
        total_income=Sum('entries__amount', filter=Q(entries__entry_type='income')),
        total_expense=Sum('entries__amount', filter=Q(entries__entry_type='expense')),
        income_count=Count('entries', filter=Q(entries__entry_type='income')),
        expense_count=Count('entries', filter=Q(entries__entry_type='expense')),
        )

        # ✅ ADD ORDERING HERE
        qs = qs.order_by('-created_at')

        return qs

    def get_organization(self, user):
        if hasattr(user, 'officer'):
            return user.officer.organization
        elif hasattr(user, 'adviser'):
            return user.adviser.organization
        elif hasattr(user, 'co_adviser'):
            return user.adviser.organization
        elif hasattr(user, 'campus_admin'):
            return getattr(user.campus_admin, 'organization', None)
        return None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        org = self.get_organization(user)

        role_templates = {
            "treasurer": "app/officer/treasurer/sidebar.html",
            "auditor": "app/officer/auditor/sidebar.html",
            "president": "app/officer/president/sidebar.html",
            "adviser": "app/adviser/sidebar.html",
            "co_adviser": "app/adviser/sidebar.html",
        }

        context['base_template'] = role_templates.get(user.role, "app/base.html")

        context['reports'] = context['object_list']

        context['rejected_reports'] = FinancialReport.objects.filter(
            organization=org, status='rejected'
        ).annotate(
            total_income=Sum('entries__amount', filter=Q(entries__entry_type='income')),
            total_expense=Sum('entries__amount', filter=Q(entries__entry_type='expense')),
            income_count=Count('entries', filter=Q(entries__entry_type='income')),
            expense_count=Count('entries', filter=Q(entries__entry_type='expense')),
        )

        context['status_choices'] = FinancialReport.STATUS_CHOICES
        return context


class ReportDetailView(RoleRequireMixin, DetailView):
    model = FinancialReport
    template_name = 'app/officer/report_details.html'
    context_object_name = 'report'
    role_required = ['treasurer', 'auditor', 'president', 'adviser', 'co_adviser']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        report = self.get_object()
        user = self.request.user


        entries = report.entries.order_by('date', 'category', 'order')

        grouped = {}
        for entry in entries:
            key = entry.date
            if key not in grouped:
                grouped[key] = {
                    'date': key,
                    'entries': [],
                    'income_subtotal': 0,
                    'expense_subtotal': 0,
                }
            grouped[key]['entries'].append(entry)
            if entry.entry_type == 'income':
                grouped[key]['income_subtotal'] += entry.amount or 0
            else:
                grouped[key]['expense_subtotal'] += entry.amount or 0

        grouped_entries = []
        for group in grouped.values():
            entries_with_meta = []
            for category, cat_entries in groupby(group['entries'], key=lambda e: e.category):
                cat_list = list(cat_entries)
                for i, entry in enumerate(cat_list):
                    entries_with_meta.append({
                        'entry':            entry,
                        'show_category':    i == 0,
                        'category_rowspan': len(cat_list) if i == 0 else None,
                    })

            grouped_entries.append({
                'date':             group['date'],
                'entries':          entries_with_meta,
                'income_subtotal':  group['income_subtotal'] or None,
                'expense_subtotal': group['expense_subtotal'] or None,
            })

        role_templates = {
            "treasurer":  "app/officer/treasurer/sidebar.html",
            "auditor":    "app/officer/auditor/sidebar.html",
            "president":  "app/officer/president/sidebar.html",
            "adviser":    "app/adviser/sidebar.html",
            "co_adviser": "app/adviser/sidebar.html",
        }

        total_income  = entries.filter(entry_type='income').aggregate(t=Sum('amount'))['t'] or 0
        total_expense = entries.filter(entry_type='expense').aggregate(t=Sum('amount'))['t'] or 0

        context['base_template']       = role_templates.get(user.role, "app/base.html")
        context['grouped_entries']     = grouped_entries
        context['approval_logs']       = report.approval_logs.order_by('created_at')
        context['total_income']        = total_income
        context['total_expense']       = total_expense
        context['net_total']           = total_income - total_expense
        context['blockchain_verified'] = verify_report_hash(report) if report.blockchain_hash else None

        return context

class ChatView(RoleRequireMixin, TemplateView):
    template_name = 'app/officer/officer_chat.html'
    role_required = ["treasurer", "auditor", "president", "adviser", "head", "co_adviser"]

    def get_organization(self, user):
        if hasattr(user, 'officer'):
            return user.officer.organization
        elif hasattr(user, 'adviser'):
            return user.adviser.organization
        elif hasattr(user, 'co_adviser'):
            return user.adviser.organization
        elif hasattr(user, 'head'):
            return getattr(user.head, 'organization', None)
        return None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        org = self.get_organization(user)

        context["global_messages"] = GlobalChat.objects.select_related(
            "user"
        ).order_by("createdAt")[:50]

        context['user_role'] = user.role

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
            "co_adviser": "app/adviser/sidebar.html",
            "head": "app/heads/sidebar.html",
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

class OrgPublicProfileView(DetailView):
    model = Organization
    template_name = "app/officer/org_profile.html"
    context_object_name = "org"

    role_template = {
       "treasurer": "app/officer/treasurer/sidebar.html",
        "auditor": "app/officer/auditor/sidebar.html",
        "president": "app/officer/president/sidebar.html",
        "adviser": "app/adviser/sidebar.html",
        "co_adviser": "app/adviser/sidebar.html",
        "head": "app/heads/sidebar.html",
    }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        org = self.object
        user = self.request.user

        officers = Officer.objects.filter(
            organization=org
        ).select_related("user")

        advisers = Adviser.objects.filter(
            organization=org
        ).select_related("user")

        announcements = OrganizationAnnouncement.objects.filter(
            organization=org
        ).select_related("author")[:5]

        context['base_template'] = self.role_template.get(user.role, 'app/base.html')
        context["org_category"] = org.category
        context["officers"] = officers
        context["advisers"] = advisers
        context["total_officers"] = officers.count()
        context["total_advisers"] = advisers.count()
        context["announcements"] = announcements
        return context
    

class ProductListView(ListView, RoleRequireMixin):
    model = Product
    template_name = 'app/officer/product_list.html'
    context_object_name = 'products'
    role_required = ["treasurer", "auditor", "president", "adviser", "co_adviser"]
    paginate_by = 10

    role_templates = {
        'treasurer' : 'app/officer/treasurer/sidebar.html',
        'auditor' : 'app/officer/auditor/sidebar.html',
        'president' : 'app/officer/president/sidebar.html',
        'adviser' : 'app/adviser/sidebar.html',
        'co_adviser' : 'app/adviser/sidebar.html',
    }

    def get_organization(self, user):
        if hasattr(user, 'officer'):
            return self.request.user.officer.organization
        elif hasattr(user, 'adviser'):
            return self.request.user.adviser.organization
        elif hasattr(user, 'co_adviser'):
            return self.request.user.adviser.organization
        
        return None
        

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        org = self.get_organization(user)
        context["base_template"] = self.role_templates.get(user.role,'app/base.html')
        context["products"] = Product.objects.filter(organization=org).annotate(
            variant_count = Count('variants')
        )
        return context
    
