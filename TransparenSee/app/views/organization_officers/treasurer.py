from django.contrib import messages
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse_lazy, reverse
from django.views.generic import TemplateView, ListView, CreateView, UpdateView, DeleteView, DetailView
from accounts.models import CustomUser
from ...blockchain import contract_abi
from django.core.paginator import Paginator
from ...models import *
from django.db.models import Q, Sum, Count
from ..mixins import *
from django.db import transaction
from django.http import JsonResponse


class TreasurerDashboardView(RoleRequireMixin, TemplateView):
    template_name = 'app/officer/treasurer/dashboard.html'
    role_required = 'treasurer'
    
    def get_organization(self):
        return self.request.user.officer.organization
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        org =  self.get_organization()
        recent_approval_log = ReportApprovalLog.objects.filter(report__organization = org).order_by('-created_at')[:3]
        context["society_fee_amount"] = org.society_fee_amount
        context["balance"] = org.balance
        context["pending_financial_reports"] = FinancialReport.objects.filter(organization=org, status='pending').exclude(status='rejected').count()
        context["approved_financial_reports"] = FinancialReport.objects.filter(organization=org, status__in=['approved', 'on_blockchain']).count()
        context["recent_approval_logs"] = recent_approval_log
        context['recent_financial_reports'] = FinancialReport.objects.filter(organization=org).exclude(status='rejected').annotate(
            income_count=Count('entries', filter=Q(entries__entry_type='income')),
            expense_count=Count('entries', filter=Q(entries__entry_type='expense')),
        ).order_by('-created_at')[:3]
        
        return context
    


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
        target_amount = fees.aggregate(total=Sum('amount'))['total'] or 0
        paid_count = fees.filter(status='paid').count()
        unpaid_count = fees.filter(status='unpaid').count()
        paid_total = fees.aggregate(total=Sum('amount_paid'))['total'] or 0 
        paid_percent = round((paid_count / total_students) * 100,2) if total_students else 0
        unpaid_percent = round((unpaid_count / total_students) * 100, 2) if total_students else 0
        paid_total_percent = round(( paid_total / target_amount ) * 100,2 ) if target_amount else 0
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
            'paid_total': paid_total,
            'paid_total_percent': paid_total_percent,
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





class CreateFinancialReportView(RoleRequireMixin, TemplateView):
    template_name = 'app/officer/treasurer/create_report.html'
    role_required = 'treasurer'

    def get_organization(self):
        return self.request.user.officer.organization

    def get(self, request):
        academic_years = AcademicYear.objects.all().order_by('-academic_year')
        return render(request, self.template_name, {
            'academic_years': academic_years
        })
    

    def post(self, request):
        org = self.get_organization()
        title = request.POST.get('title', '').strip()
        academic_year_id = request.POST.get('academic_year')

        if not title:
            messages.error(request, 'Title is required.')
            return redirect(request.path)

        dates        = request.POST.getlist('date[]')
        categories   = request.POST.getlist('category[]')
        descriptions = request.POST.getlist('description[]')
        amounts      = request.POST.getlist('amount[]')
        entry_types  = request.POST.getlist('entry_type[]')
        income_sources      = request.POST.getlist('income_source[]')
        society_semesters   = request.POST.getlist('society_semester[]')
        society_ay_ids      = request.POST.getlist('society_academic_year[]')

        if not dates:
            messages.error(request, 'At least one entry is required.')
            return redirect(request.path)

        with transaction.atomic():
            ay = AcademicYear.objects.get(pk=academic_year_id) if academic_year_id else None

            report = FinancialReport.objects.create(
                organization=org,
                created_by=request.user,
                academic_year=ay,
                title=title,
                status='pending_auditor',
            )

            entries = []
            for i, (date, category, description, amount) in enumerate(
                zip(dates, categories, descriptions, amounts)
            ):
                if not (date and amount):
                    continue

                entry_type    = entry_types[i] if i < len(entry_types) else 'expense'
                income_source = income_sources[i] if i < len(income_sources) else None
                soc_semester  = society_semesters[i] if i < len(society_semesters) else None
                soc_ay_id     = society_ay_ids[i] if i < len(society_ay_ids) else None

                student_count    = None
                fee_per_student  = None
                stored_semester  = None

                # If this row is a society fee income entry, snapshot the data
                if entry_type == 'income' and income_source == 'society' and soc_ay_id and soc_semester:
                    soc_ay = AcademicYear.objects.filter(pk=soc_ay_id).first()
                    if soc_ay:
                        paid_fees = SocietyFee.objects.filter(
                            organization=org,
                            academic_year=soc_ay,
                            semester=soc_semester,
                            status='paid',
                        )
                        student_count   = paid_fees.count()
                        fee_per_student = org.society_fee_amount
                        stored_semester = soc_semester

                entries.append(FinancialReportEntry(
                    report=report,
                    date=date,
                    category=category,
                    description=description,
                    amount=amount,
                    order=i,
                    entry_type=entry_type,
                    income_source=income_source if entry_type == 'income' else None,
                    society_student_count=student_count,
                    society_fee_per_student=fee_per_student,
                    society_semester=stored_semester,
                ))

            FinancialReportEntry.objects.bulk_create(entries)

            ReportApprovalLog.objects.create(
                report=report,
                action_by=request.user,
                action='submitted',
                remarks='Report submitted for approval.'
            )

        return redirect(f"{reverse('reports')}?submitted=1")


class SocietyFeePreviewView(RoleRequireMixin, TemplateView):

    role_required = 'treasurer'

    def get(self, request):
        org = request.user.officer.organization
        ay_id = request.GET.get('academic_year')

        if not ay_id:
            return JsonResponse({'error': 'Missing academic year.'}, status=400)

        ay = AcademicYear.objects.filter(pk=ay_id).first()
        if not ay:
            return JsonResponse({'error': 'Academic year not found.'}, status=404)

        paid_fees = SocietyFee.objects.filter(
            organization=org,
            academic_year=ay,
            semester=ay.semester,   # <-- pulled from AcademicYear directly
            status='paid',
        )
        student_count   = paid_fees.count()
        fee_per_student = float(org.society_fee_amount)
        total           = student_count * fee_per_student

        return JsonResponse({
            'student_count':   student_count,
            'fee_per_student': fee_per_student,
            'total':           total,
            'academic_year':   str(ay),
            'semester':        ay.semester,   # pass back so JS can store it
        })