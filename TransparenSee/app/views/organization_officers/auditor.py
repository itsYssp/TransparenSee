import calendar
import re
from collections import OrderedDict
from datetime import date, datetime
from decimal import Decimal
from django.db.models import Count, Q, Sum
from django.http import JsonResponse
from django.views.generic import TemplateView

from ...blockchain import get_all_transactions, verify_report_hash
from ...models import AcademicYear, FinancialReport, FinancialReportEntry, Product, ReportApprovalLog
from ..mixins import RoleRequireMixin


class AuditorDashboardView(RoleRequireMixin, TemplateView):
    template_name = 'app/officer/auditor/dashboard.html'
    role_required = 'auditor'

    def get_organization(self):
        return self.request.user.officer.organization

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        org = self.get_organization()
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
        return context


class StatementPeriodMixin:
    @staticmethod
    def _academic_year_bounds(academic_year):
        if not academic_year:
            return None

        match = re.search(r"(\d{4})\D+(\d{4})", academic_year.academic_year or "")
        if not match:
            return None

        return int(match.group(1)), int(match.group(2))

    @staticmethod
    def _safe_int(value):
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _last_day_of_month(year, month):
        return calendar.monthrange(year, month)[1]

    def build_period_context(self, request):
        period_type = request.GET.get('period_type') or request.POST.get('period_type') or ''
        context = {
            "period_type": period_type,
            "label": "All Available Records",
            "start_date": None,
            "end_date": None,
            "academic_year_obj": None,
            "academic_year_id": None,
            "academic_year_label": None,
            "error": None,
        }

        if not period_type:
            context["error"] = "Select a reporting period."
            return context

        if period_type == 'monthly':
            month = self._safe_int(request.GET.get('month') or request.POST.get('month'))
            year = self._safe_int(request.GET.get('year') or request.POST.get('year'))
            if not month or not year:
                context["error"] = "Month and year are required for monthly statements."
                return context
            start_date = date(year, month, 1)
            end_date = date(year, month, self._last_day_of_month(year, month))
            context.update({
                "label": start_date.strftime("%B %Y"),
                "start_date": start_date,
                "end_date": end_date,
            })
            return context

        if period_type in {'semestral', 'yearly'}:
            if period_type == 'semestral':
                academic_year_id = (
                    request.GET.get('academic_year_period')
                    or request.GET.get('academic_year')
                    or request.POST.get('academic_year_period')
                    or request.POST.get('academic_year')
                )
                academic_year = AcademicYear.objects.filter(pk=academic_year_id).first() if academic_year_id else None
                bounds = self._academic_year_bounds(academic_year)
                if not academic_year or not bounds:
                    context["error"] = "Select a valid semestral academic year."
                    return context
                start_year, end_year = bounds
                if academic_year.semester == '1stSem':
                    start_date = date(start_year, 8, 1)
                    end_date = date(start_year, 12, 31)
                else:
                    start_date = date(end_year, 1, 1)
                    end_date = date(end_year, 5, 31)
                label = str(academic_year)
                context.update({
                    "label": label,
                    "start_date": start_date,
                    "end_date": end_date,
                    "academic_year_obj": academic_year,
                    "academic_year_id": academic_year.id,
                    "academic_year_label": academic_year.academic_year,
                })
                return context
            else:
                academic_year_label = (
                    request.GET.get('academic_year_yearly')
                    or request.GET.get('academic_year')
                    or request.POST.get('academic_year_yearly')
                    or request.POST.get('academic_year')
                )
                academic_year = AcademicYear.objects.filter(academic_year=academic_year_label).order_by('semester').first() if academic_year_label else None
                bounds = self._academic_year_bounds(academic_year)
                if not academic_year_label or not bounds:
                    context["error"] = "Select a valid yearly academic year."
                    return context
                start_year, end_year = bounds
                start_date = date(start_year, 8, 1)
                end_date = date(end_year, 7, 31)
                label = f"A.Y. {academic_year_label}"

            context.update({
                "label": label,
                "start_date": start_date,
                "end_date": end_date,
                "academic_year_obj": academic_year,
                "academic_year_id": academic_year.id if academic_year else None,
                "academic_year_label": academic_year_label if period_type == 'yearly' else academic_year.academic_year,
            })
            return context

        if period_type == 'event':
            event_name = (request.GET.get('event_name') or request.POST.get('event_name') or '').strip()
            start_raw = request.GET.get('event_date_from') or request.POST.get('event_date_from')
            end_raw = request.GET.get('event_date_to') or request.POST.get('event_date_to')
            if not start_raw or not end_raw:
                context["error"] = "Event start and end dates are required."
                return context

            start_date = datetime.strptime(start_raw, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_raw, "%Y-%m-%d").date()
            if start_date > end_date:
                context["error"] = "Event start date must be earlier than the end date."
                return context

            label = event_name or f"{start_date:%b %d, %Y} to {end_date:%b %d, %Y}"
            context.update({
                "label": label,
                "start_date": start_date,
                "end_date": end_date,
            })
            return context

        context["error"] = "Unsupported reporting period."
        return context

    @staticmethod
    def _entry_quantity(entry):
        if entry.unit_price and entry.unit_price != 0:
            quantity = Decimal(entry.amount) / Decimal(entry.unit_price)
            if quantity == quantity.to_integral_value():
                return int(quantity)
            return float(quantity.quantize(Decimal("0.01")))
        return 1

    def build_statement_payload(self, request, organization):
        period = self.build_period_context(request)
        payload = {
            "period": period,
            "entries": [],
            "report_summaries": [],
            "total_income": 0.0,
            "total_expense": 0.0,
            "net_total": 0.0,
            "current_balance": float(organization.balance or 0),
            "record_count": 0,
            "report_count": 0,
        }

        if period["error"]:
            return payload

        reports = FinancialReport.objects.filter(
            organization=organization,
            status = 'on_blockchain'
        ).select_related(
            'academic_year', 'created_by'
        ).prefetch_related(
            'entries'
        ).order_by('title', 'created_at')

        if period["period_type"] == 'semestral' and period["academic_year_obj"]:
            reports = reports.filter(academic_year=period["academic_year_obj"])
            entries = FinancialReportEntry.objects.filter(
                report__in=reports,
            )
        elif period["period_type"] == 'yearly' and period["academic_year_label"]:
            reports = reports.filter(academic_year__academic_year=period["academic_year_label"])
            entries = FinancialReportEntry.objects.filter(
                report__in=reports,
            )
        else:
            entries = FinancialReportEntry.objects.filter(
                report__in=reports,
                date__gte=period["start_date"],
                date__lte=period["end_date"],
            )

        entries = entries.select_related('report', 'report__academic_year').order_by(
            'report__title', 'date', 'order', 'id'
        )

        report_ids = list(OrderedDict.fromkeys(entry.report_id for entry in entries))
        relevant_reports = [report for report in reports if report.id in report_ids]

        summaries = []
        for report in relevant_reports:
            report_entries = [entry for entry in entries if entry.report_id == report.id]
            total_income = sum(float(entry.amount) for entry in report_entries if entry.entry_type == 'income')
            total_expense = sum(float(entry.amount) for entry in report_entries if entry.entry_type == 'expense')
            blockchain_verified = verify_report_hash(report) if report.blockchain_hash else None
            summaries.append({
                "id": report.id,
                "title": report.title,
                "status": report.status,
                "academic_year": str(report.academic_year) if report.academic_year else "—",
                "blockchain_hash": report.blockchain_hash or "",
                "blockchain_verified": blockchain_verified,
                "income": total_income,
                "expense": total_expense,
                "net": total_income - total_expense,
            })

        rows = []
        for entry in entries:
            rows.append({
                "report_id": entry.report_id,
                "report_title": entry.report.title,
                "report_status": entry.report.status,
                "date": entry.date.strftime("%Y-%m-%d"),
                "category": entry.category,
                "description": entry.description,
                "entry_type": entry.entry_type,
                "quantity": self._entry_quantity(entry),
                "unit_price": float(entry.unit_price or 0),
                "amount": float(entry.amount or 0),
            })

        total_income = sum(row["amount"] for row in rows if row["entry_type"] == 'income')
        total_expense = sum(row["amount"] for row in rows if row["entry_type"] == 'expense')

        payload.update({
            "entries": rows,
            "report_summaries": summaries,
            "total_income": total_income,
            "total_expense": total_expense,
            "net_total": total_income - total_expense,
            "record_count": len(rows),
            "report_count": len(summaries),
        })
        return payload


class GenerateFinancialStatementView(RoleRequireMixin, TemplateView):
    template_name = 'app/officer/auditor/generate_fs.html'
    role_required = 'auditor'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        officer = self.request.user.officer
        organization = officer.organization
        context['academic_years'] = AcademicYear.objects.all().order_by('-academic_year', 'semester')
        context['semestral_academic_years'] = AcademicYear.objects.all().order_by('-academic_year', 'semester')
        context['yearly_academic_years'] = AcademicYear.objects.order_by('-academic_year').values_list('academic_year', flat=True).distinct()
        context['products'] = Product.objects.filter(
            organization=organization,
            is_active=True
        ).prefetch_related('variants')
        context['organization'] = organization
        context['today_year'] = date.today().year
        return context


class FinancialStatementDataView(RoleRequireMixin, StatementPeriodMixin, TemplateView):
    role_required = 'auditor'

    def get(self, request, *args, **kwargs):
        organization = request.user.officer.organization
        payload = self.build_statement_payload(request, organization)
        if payload.get("period"):
            payload["period"] = {
                key: value
                for key, value in payload["period"].items()
                if key != "academic_year_obj"
            }
        return JsonResponse(payload)


class PrintableFinancialStatementView(RoleRequireMixin, StatementPeriodMixin, TemplateView):
    template_name = 'app/officer/auditor/financial_statement_print.html'
    role_required = 'auditor'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        organization = self.request.user.officer.organization
        payload = self.build_statement_payload(self.request, organization)
        context.update(payload)
        context['organization'] = organization
        context['prepared_by'] = self.request.user.get_full_name() or self.request.user.username
        context['generated_at'] = datetime.now()
        context['auto_print'] = self.request.GET.get('auto_print') == '1'
        return context


class BlockchainFinancialRecordsView(TemplateView):
    def get(self, request):
        try:
            txs = get_all_transactions()
            officer_org = None
            if request.user.is_authenticated and hasattr(request.user, "officer"):
                officer_org = request.user.officer.organization.name

            records = []
            for tx in txs:
                tx_datetime = datetime.fromtimestamp(tx[3])
                if officer_org and tx[0] != officer_org:
                    continue

                records.append({
                    "org": tx[0],
                    "amount": float(tx[1]) / 100,
                    "sender": tx[2],
                    "date": tx_datetime.strftime("%Y-%m-%d %H:%M:%S"),
                    "tx_hash": tx[4],
                    "title": tx[5],
                })

            records.sort(key=lambda item: item["date"], reverse=True)
            return JsonResponse({"records": records})
        except Exception as e:
            return JsonResponse({
                "error": str(e),
                "records": []
            }, status=500)
