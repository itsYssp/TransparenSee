from django.utils import timezone 
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import TemplateView, ListView, CreateView, UpdateView, DeleteView, DetailView
from ...forms import *
from ..mixins import *
from django.db.models import Sum, Q, Count 
from ...blockchain import verify_report_hash



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

        role_templates= {
            "treasurer": "app/officer/treasurer/sidebar.html",
            "auditor": "app/officer/auditor/sidebar.html",
            "president": "app/officer/president/sidebar.html",
            "adviser": "app/adviser/sidebar.html",
            "co_adviser": "app/adviser/sidebar.html",
        }
 
        context['base_template'] = role_templates.get(user.role, "app/base.html")
        context['reports'] = FinancialReport.objects.filter(organization=org).exclude(status='rejected').annotate(
            total_income=Sum('entries__amount', filter=Q(entries__entry_type='income')),
            total_expense=Sum('entries__amount', filter=Q(entries__entry_type='expense')),
            income_count=Count('entries', filter=Q(entries__entry_type='income')),
            expense_count=Count('entries', filter=Q(entries__entry_type='expense')),
        )
        context['rejected_reports'] = FinancialReport.objects.filter(organization=org, status='rejected').annotate(
            total_income=Sum('entries__amount', filter=Q(entries__entry_type='income')),
            total_expense=Sum('entries__amount', filter=Q(entries__entry_type='expense')),
            income_count=Count('entries', filter=Q(entries__entry_type='income')),
            expense_count=Count('entries', filter=Q(entries__entry_type='expense')),
        )
        context['status_choices'] = FinancialReport.STATUS_CHOICES
        return context
    
class ReportListView(ListView):
    model = FinancialReport
    template_name = 'app/officer/treasurer/report_list.html'
    paginate_by = 10

    def get_organization(self):
        user = self.request.user
        if hasattr(user, 'officer'):
            return user.officer.organization
        elif hasattr(user, 'adviser'):
            return user.adviser.organization
        elif hasattr(user, 'co_adviser'):
            return user.adviser.organization
        elif hasattr(user, 'campus_admin'):
            return getattr(user.campus_admin, 'organization', None)
        return None



    def get_annotated_reports(self, org):
        """Reusable annotation query to avoid repetition."""
        return FinancialReport.objects.filter(organization=org).annotate(
            total_income=Sum('entries__amount', filter=Q(entries__entry_type='income')),
            total_expense=Sum('entries__amount', filter=Q(entries__entry_type='expense')),
            income_count=Count('entries', filter=Q(entries__entry_type='income')),
            expense_count=Count('entries', filter=Q(entries__entry_type='expense')),
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        org = self.get_organization()

        

        role_templates = {
            "treasurer": "app/officer/treasurer/sidebar.html",
            "auditor":   "app/officer/auditor/sidebar.html",
            "president": "app/officer/president/sidebar.html",
            "adviser":   "app/adviser/sidebar.html",
            "co_adviser":   "app/adviser/sidebar.html",
        }

        context['base_template'] = role_templates.get(user.role, "app/base.html")
        context['status_choices'] = FinancialReport.STATUS_CHOICES

        search = self.request.GET.get('search', '').strip()
        status = self.request.GET.get('status', '').strip()

        if org:
            base_qs = self.get_annotated_reports(org)

            reports = base_qs.exclude(status='rejected')
            if search:
                reports = reports.filter(title__icontains=search)
            if status:
                reports = reports.filter(status=status)

            rejected = base_qs.filter(status='rejected')
            if search:
                rejected = rejected.filter(title__icontains=search)

            context['reports'] = reports
            context['rejected_reports'] = rejected
        else:
            context['reports'] = FinancialReport.objects.none()
            context['rejected_reports'] = FinancialReport.objects.none()

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

        entries = report.entries.all()
        grouped = {}
        date_subtotals = {}

        for entry in entries:
            key = entry.date
            if key not in grouped:
                grouped[key] = []
                date_subtotals[key] = 0
            grouped[key].append(entry)
            date_subtotals[key] += entry.amount or 0

        grouped_entries = []
        for date, date_entries in grouped.items():
            grouped_entries.append({
                'date': date,
                'entries': date_entries,
                'subtotal': date_subtotals[date],
            })

        role_templates = {
            "treasurer": "app/officer/treasurer/sidebar.html",
            "auditor": "app/officer/auditor/sidebar.html",
            "president": "app/officer/president/sidebar.html",
            "adviser": "app/adviser/sidebar.html",
            "co_adviser": "app/adviser/sidebar.html",
        }

        context['base_template'] = role_templates.get(user.role, "app/base.html")
        context['grouped_entries'] = grouped_entries
        context['approval_logs'] = report.approval_logs.all()
        context['total_amount'] = sum(entry.amount for entry in entries)
        entries = report.entries.all()
        context['total_income']  = entries.filter(entry_type='income').aggregate(t=Sum('amount'))['t'] or 0
        context['total_expense'] = entries.filter(entry_type='expense').aggregate(t=Sum('amount'))['t'] or 0
        context['net_total']     = context['total_income'] - context['total_expense']

        if report.blockchain_hash:
            context['blockchain_verified'] = verify_report_hash(report)
        else:
            context['blockchain_verified'] = None  # None = not yet on blockchain

        return context


class ChatView(RoleRequireMixin, TemplateView):
    template_name = 'app/officer/officer_chat.html'
    role_required = ["treasurer", "auditor", "president", "adviser", "campus_admin", "co_adviser"]

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
            "co_adviser": "app/adviser/sidebar.html",
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
    
