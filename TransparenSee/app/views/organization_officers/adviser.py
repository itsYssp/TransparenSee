from django.utils import timezone
from django.views.generic import TemplateView
from ..mixins import *
from ...blockchain import record_financial_report_on_blockchain
from django.shortcuts import get_object_or_404, redirect 
from ...models import *
from django.contrib import messages
from django.db.models import Count, Q, Sum
from django.contrib.auth import update_session_auth_hash
from ...forms import AdviserForm


class AdviserDashboardView(RoleRequireMixin, TemplateView):
    template_name = 'app/adviser/dashboard.html'
    role_required = ['adviser', 'co_adviser']

    def get_organization(self):
        return self.request.user.adviser.organization

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        org = self.get_organization()
        reports = FinancialReport.objects.filter(
            organization=org,
            status__in=['approved', 'on_blockchain']
        )

        total_income = reports.aggregate(
            total=Sum('entries__amount', filter=Q(entries__entry_type='income'))
        )['total'] or 0

        total_expense = reports.aggregate(
            total=Sum('entries__amount', filter=Q(entries__entry_type='expense'))
        )['total'] or 0

        expense_percent = round(total_expense / total_income * 100,2) if total_income > 0 else 0
        total = (total_income or 0) + (total_expense or 0)

        income_percent = round(total_income / total * 100,2) if total > 0 else 0
        
        context['total_expense'] = total_expense 
        context['expense_percent'] = expense_percent
        context['total_income'] = total_income 
        context['income_percent'] = income_percent
        recent_approval_logs = ReportApprovalLog.objects.filter(report__organization=org).order_by('-created_at')[:3]
        context["pending_financial_reports"] = FinancialReport.objects.filter(organization=org).exclude(status__in=['rejected', 'approved', 'on_blockchain']).count()
        context["approved_financial_reports"] = FinancialReport.objects.filter(organization=org, status='on_blockchain').count()
        context["flagged_financial_reports"] = FinancialReport.objects.filter(organization=org, status='rejected').count()
        context['recent_financial_reports'] = FinancialReport.objects.filter(organization=org).exclude(status='rejected').annotate(
            income_count=Count('entries', filter=Q(entries__entry_type='income')),
            expense_count=Count('entries', filter=Q(entries__entry_type='expense')),
        ).order_by('-created_at')[:3]
        context["society_fee_amount"] = org.society_fee_amount
        context["recent_approval_logs"] = recent_approval_logs
        context["organization"] = org
        context['balance'] = org.balance
        context['accomplishment_report'] = AccomplishmentReport.objects.filter(organization=org)[:3]
        return context
    

class RecordBlockchainView(RoleRequireMixin, TemplateView):
    role_required = ['adviser', 'co_adviser']

    def post(self, request, pk):
        report = get_object_or_404(FinancialReport, pk=pk)

        # Only allow if report is fully approved
        if report.status != 'approved':
            messages.error(request, 'Report must be fully approved before recording on blockchain.')
            return redirect('report_detail', pk=pk)

        # Prevent duplicate blockchain recording
        if report.blockchain_hash:
            messages.warning(request, 'This report is already recorded on the blockchain.')
            return redirect('report_detail', pk=pk)

        try:
            result = record_financial_report_on_blockchain(report)

            report.blockchain_hash        = result['report_hash']
            report.blockchain_recorded_at = timezone.now()
            report.status                 = 'on_blockchain'
            report.save(update_fields=[
                'blockchain_hash',
                'blockchain_recorded_at',
                'status',
            ])

            ReportApprovalLog.objects.create(
                report=report,
                action_by=request.user,
                action='blockchain',
                remarks=(
                    f"TX Hash: {result['tx_hash']} | "
                    f"Block: {result['block_number']} | "
                    f"Report Hash: {result['report_hash']}"
                )
            )

            messages.success(
                request,
                f"Successfully recorded on blockchain. TX: {result['tx_hash']}"
            )

        except ConnectionError as e:
            messages.error(request, f"Blockchain connection failed: {str(e)}")
        except RuntimeError as e:
            messages.error(request, f"Blockchain transaction failed: {str(e)}")
        except Exception as e:
            messages.error(request, f"Unexpected error: {str(e)}")

        return redirect('report_detail', pk=pk)

class AdviserProfileView(RoleRequireMixin, TemplateView):
    template_name = 'app/adviser/adviser_profile.html'
    role_required = ['adviser', 'co_adviser']
    role_templates = {
        'adviser': 'app/adviser/sidebar.html',
        'co_adviser': 'app/adviser/sidebar.html',
    }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context["base_template"] = self.role_templates.get(user.role, 'app/base.html')
        return context
    
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

        adviser, _ = Adviser.objects.get_or_create(user=request.user)
        form = AdviserForm(request.POST, request.FILES, instance=adviser)

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
    

