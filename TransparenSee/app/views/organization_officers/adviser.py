from django.utils import timezone
from django.views.generic import TemplateView
from ..mixins import *
from ...blockchain import record_financial_report_on_blockchain
from django.shortcuts import get_object_or_404, redirect 
from ...models import *
from django.contrib import messages

class AdviserDashboardView(RoleRequireMixin, TemplateView):
    template_name = 'app/adviser/dashboard.html'
    role_required = ['adviser', 'co_adviser']

    def get_organization(self):
        return self.request.user.adviser.organization

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        org = self.get_organization()
        context["balance"] =  org.balance
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
    

