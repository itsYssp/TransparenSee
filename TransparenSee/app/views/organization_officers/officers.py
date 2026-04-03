from django.utils import timezone 

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import TemplateView, ListView, CreateView, UpdateView, DeleteView, DetailView
from ...forms import *
from ..mixins import *


class ApproveReportView(RoleRequireMixin, TemplateView):
    role_required = ['auditor', 'president', 'adviser']

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


        search = self.request.GET.get('search')
        if search:
            qs = qs.filter(title__icontains=search)


        status = self.request.GET.get('status')
        if status:
            qs = qs.filter(status=status)

        return qs

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
        role_templates= {
            "treasurer": "app/officer/treasurer/sidebar.html",
            "auditor": "app/officer/auditor/sidebar.html",
            "president": "app/officer/president/sidebar.html",
            "adviser": "app/adviser/sidebar.html",
        }
 
        context['base_template'] = role_templates.get(user.role, "app/base.html")
        context['reports'] = FinancialReport.objects.filter(organization=org).exclude(status='rejected')
        context['rejected_reports'] = FinancialReport.objects.filter(organization=org, status='rejected')
        context['status_choices'] = FinancialReport.STATUS_CHOICES
        return context
    
class ReportDetailView(RoleRequireMixin, DetailView):
    model = FinancialReport
    template_name = 'app/officer/report_details.html'
    context_object_name = 'report'
    role_required = ['treasurer', 'auditor', 'president', 'adviser']

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
        }

        context['base_template'] = role_templates.get(user.role, "app/base.html")
        context['grouped_entries'] = grouped_entries
        context['approval_logs'] = report.approval_logs.all()
        context['total_amount'] = sum(entry.amount for entry in entries)
        return context


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
    
