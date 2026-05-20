from django.contrib import messages
from django.shortcuts import get_object_or_404, render, redirect
from django.views.generic import TemplateView, ListView, CreateView, UpdateView, DeleteView, DetailView
from ..forms import *
from ..blockchain import contract_abi
from datetime import datetime
from web3 import Web3
from django.core.paginator import Paginator
from web3.middleware.geth_poa import geth_poa_middleware
from django.contrib.auth import update_session_auth_hash
import os
from dotenv import load_dotenv
from ..models import *
from .mixins import *
from django.db.models import Prefetch, Sum, Q
from ..blockchain import verify_report_hash
from ..blockchain_utils import build_report_snapshot, generate_report_hash
from decimal import Decimal
import re

class StudentDashboardView(RoleRequireMixin, TemplateView):
    template_name = "app/student/dashboard.html"
    role_required = 'student'

    def get_organization(self, user):
        return user.student.organization

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

    def get(self, request):
        context = self.get_context_data()
        user = request.user
        org = self.get_organization(user)

        # ── Active tab ─────────────────────────────────────────────
        active_tab = request.GET.get('type', 'financial')

        # ── Blockchain / Financial records ─────────────────────────
        base_qs = FinancialReport.objects.filter(
            status='on_blockchain'
        ).prefetch_related(
            'entries',
            Prefetch(
                'approval_logs',
                queryset=ReportApprovalLog.objects.filter(
                    action='blockchain'
                ).select_related('action_by').order_by('-created_at'),
                to_attr='blockchain_logs'
            )
        ).order_by('-blockchain_recorded_at')

        if org:
            base_qs = base_qs.filter(organization=org)

        reports = list(base_qs)

        trusted_count  = 0
        tampered_count = 0

        for report in reports:
            report.total_income  = report.entries.filter(entry_type='income').aggregate(t=Sum('amount'))['t'] or 0
            report.total_expense = report.entries.filter(entry_type='expense').aggregate(t=Sum('amount'))['t'] or 0
            report.net           = report.total_income - report.total_expense

            report.is_verified = verify_report_hash(report)

            if not report.is_verified and report.blockchain_hash:
                snapshot = build_report_snapshot(report)
                report.recomputed_hash = generate_report_hash(snapshot)
            else:
                report.recomputed_hash = None

            if report.is_verified:
                trusted_count += 1
            else:
                tampered_count += 1
            blockchain_log = report.blockchain_logs[0] if report.blockchain_logs else None
            report.blockchain_remarks = blockchain_log.remarks if blockchain_log else None
            report.blockchain_recorded_by = blockchain_log.action_by if blockchain_log else None

            tx_hash = None
            if blockchain_log and blockchain_log.remarks:
                match = re.search(r"TX Hash:\s*([a-f0-9]+)", blockchain_log.remarks, re.IGNORECASE)
                if match:
                    tx_hash = match.group(1)

            report.tx_hash = tx_hash

        # ── All financial reports (for the financial tab table) ────
        financial_reports = FinancialReport.objects.filter(
            organization=org
        ).prefetch_related('entries').order_by('-created_at') if org else FinancialReport.objects.none()

        # ── Accomplishment reports ─────────────────────────────────
        accomplishment_report = AccomplishmentReport.objects.filter(
            organization=org
        ).order_by('-created_at') if org else AccomplishmentReport.objects.none()

        context.update({
            'active_tab':           active_tab,
            'reports':              reports,
            'financial_reports':    financial_reports,
            'accomplishment_report': accomplishment_report,
            'total_income':         sum(r.total_income  for r in reports),
            'total_expense':        sum(r.total_expense for r in reports),
            'academic_years':       AcademicYear.objects.order_by('-academic_year'),
            'trusted_count':        trusted_count,
            'tampered_count':       tampered_count,
            'tx_count':             len(reports),
        })

        return render(request, self.template_name, context)
    
class MembersView(RoleRequireMixin, TemplateView):
    template_name = "app/officer/members.html"
    role_required = ['president', 'treasurer', 'auditor', 'adviser', 'co_adviser', 'vice_president', 'secretary']

    role_templates = {
        'treasurer':      'app/officer/treasurer/sidebar.html',
        'auditor':        'app/officer/auditor/sidebar.html',
        'president':      'app/officer/president/sidebar.html',
        'vice_president': 'app/officer/president/sidebar.html',
        'co_adviser':     'app/adviser/sidebar.html',
        'adviser':        'app/adviser/sidebar.html',
        'secretary':      'app/officer/secretary/sidebar.html',
    }

    def get_organization(self):
        user = self.request.user
        if hasattr(user, 'officer'):
            return user.officer.organization
        if hasattr(user, 'adviser'):
            return user.adviser.organization
        return None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        org = self.get_organization()
        user = self.request.user
        context['base_template'] = self.role_templates.get(user.role, 'app/base.html')

        if org.category == 'academic':
            students_qs = CustomUser.objects.filter(
                student__organization=org
            ).order_by('-date_joined')
        else:
            students_qs = CustomUser.objects.filter(
                student__other_organization=org
            ).order_by('-date_joined')

        paginator = Paginator(students_qs, 10)
        page_number = self.request.GET.get('page', 1)
        context['students'] = paginator.get_page(page_number)
        context['page_obj'] = paginator.get_page(page_number)

        return context

class OtherOrganizationDashboardView(RoleRequireMixin, DetailView):
    template_name = 'app/student/other_org_dashboard.html'
    role_required = 'student'
    model = Organization
    context_object_name = 'other'

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        user = self.request.user

        allowed_orgs = set()

        if hasattr(user, 'student') and user.student.organization:
            allowed_orgs.add(user.student.organization.pk)

        if hasattr(user, 'student'):
            other_org_pks = user.student.other_organization.values_list('pk', flat=True)
            allowed_orgs.update(other_org_pks)

        if obj.pk not in allowed_orgs:
            raise PermissionDenied

        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        org = self.object

        active_tab = self.request.GET.get('type', 'financial')

        # ── Blockchain records ───────────────────────────────
        base_qs = FinancialReport.objects.filter(
            status='on_blockchain',
            organization=org
        ).prefetch_related(
            'entries',
            Prefetch(
                'approval_logs',
                queryset=ReportApprovalLog.objects.filter(
                    action='blockchain'
                ).select_related('action_by').order_by('-created_at'),
                to_attr='blockchain_logs'
            )
        ).order_by('-blockchain_recorded_at')

        trusted_count = 0
        tampered_count = 0

        reports = base_qs  # keep queryset (no need for list)

        for report in reports:
            # ── financial computation ──
            report.total_income = report.entries.filter(
                entry_type='income'
            ).aggregate(t=Sum('amount'))['t'] or 0

            report.total_expense = report.entries.filter(
                entry_type='expense'
            ).aggregate(t=Sum('amount'))['t'] or 0

            report.net = report.total_income - report.total_expense

            # ── verification ──
            report.is_verified = verify_report_hash(report)

            if not report.is_verified and report.blockchain_hash:
                snapshot = build_report_snapshot(report)
                report.recomputed_hash = generate_report_hash(snapshot)
            else:
                report.recomputed_hash = None

            # ── counters ──
            if report.is_verified:
                trusted_count += 1
            else:
                tampered_count += 1

            # ── blockchain log (latest) ──
            blockchain_log = report.blockchain_logs[0] if report.blockchain_logs else None

            report.blockchain_remarks = blockchain_log.remarks if blockchain_log else None
            report.blockchain_recorded_by = blockchain_log.action_by if blockchain_log else None

            # ── TX HASH extraction from remarks ──
            tx_hash = None
            if blockchain_log and blockchain_log.remarks:
                match = re.search(
                    r"TX Hash:\s*([a-f0-9]+)",
                    blockchain_log.remarks,
                    re.IGNORECASE
                )
                if match:
                    tx_hash = match.group(1)

            report.tx_hash = tx_hash

        # ── Financial reports (tab table) ──
        financial_reports = FinancialReport.objects.filter(
            organization=org
        ).prefetch_related('entries').order_by('-created_at')

        # ── Accomplishment reports ──
        accomplishment_report = AccomplishmentReport.objects.filter(
            organization=org
        ).order_by('-created_at')

        context.update({
            'active_tab': active_tab,
            'reports': reports,
            'financial_reports': financial_reports,
            'accomplishment_report': accomplishment_report,
            'total_income': sum(r.total_income for r in reports),
            'total_expense': sum(r.total_expense for r in reports),
            'academic_years': AcademicYear.objects.order_by('-academic_year'),
            'trusted_count': trusted_count,
            'tampered_count': tampered_count,
            'tx_count': len(list(reports)),  # safe count
            'current_org_pk': self.object.pk,
        })

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