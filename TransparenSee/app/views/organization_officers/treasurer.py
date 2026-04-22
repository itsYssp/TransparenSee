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
from decimal import Decimal

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
        context["pending_financial_reports"] = FinancialReport.objects.filter(organization=org).exclude(status__in=['rejected','approved', 'on_blockchain']).count()
        context["approved_financial_reports"] = FinancialReport.objects.filter(organization=org, status__in=['approved', 'on_blockchain']).count()
        context["recent_approval_logs"] = recent_approval_log
        context['recent_financial_reports'] = FinancialReport.objects.filter(organization=org).exclude(status='rejected').annotate(
            income_count=Count('entries', filter=Q(entries__entry_type='income')),
            expense_count=Count('entries', filter=Q(entries__entry_type='expense')),
        ).order_by('-created_at')[:3]
        
        return context
    

class SocietyFeeView(RoleRequireMixin, TemplateView):
    template_name = 'app/officer/treasurer/society_fee.html'
    role_required = ['treasurer', 'auditor', 'president', 'adviser', 'co_adviser']

    role_templates = {
        'treasurer': 'app/officer/treasurer/sidebar.html',
        'auditor': 'app/officer/auditor/sidebar.html',
        'president': 'app/officer/president/sidebar.html',
        'adviser': 'app/adviser/sidebar.html',
        'co_adviser': 'app/adviser/sidebar.html',
    }

    def get_organization(self):
        user = self.request.user
        if hasattr(user, 'officer'):
            return user.officer.organization
        elif hasattr(user, 'adviser'):
            return user.adviser.organization
        elif hasattr(user, 'co_adviser'):
            return user.adviser.organization
        return None

    def get_context_data(self, **kwargs):
        user = self.request.user
        context = super().get_context_data(**kwargs)
        context["base_template"] = self.role_templates.get(user.role, 'app/base.html') 
        return context
    
    def get(self, request, *args, **kwargs):
        context = self.get_context_data()
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
        status = request.GET.get('status', '')

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
        if status: 
            fees = fees.filter(status=status)

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

        context.update({
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

        return render(request, self.template_name, context)

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
        org = self.get_organization()
        academic_years = AcademicYear.objects.all().order_by('-academic_year')
        products = Product.objects.filter(organization=org)
        return render(request, self.template_name, {
            'academic_years': academic_years,
            'products': products,
        })

    def post(self, request):
        org   = self.get_organization()
        title = request.POST.get('title', '').strip()
        academic_year_id = request.POST.get('academic_year')

        if not title:
            messages.error(request, 'Title is required.')
            return redirect(request.path)

        dates          = request.POST.getlist('date[]')
        categories     = request.POST.getlist('category[]')
        descriptions   = request.POST.getlist('description[]')
        amounts        = request.POST.getlist('amount[]')
        entry_types    = request.POST.getlist('entry_type[]')
        income_sources = request.POST.getlist('income_source[]')
        society_ay_ids = request.POST.getlist('society_academic_year[]')
        product_ids    = request.POST.getlist('product_id[]')
        variant_ids    = request.POST.getlist('variant_id[]')
        quantities     = request.POST.getlist('quantity[]')  
        unit_prices     = request.POST.getlist('unit_price[]')

        if not any(d.strip() for d in dates):
            messages.error(request, 'At least one entry is required.')
            return redirect(request.path)

        with transaction.atomic():
            ay = AcademicYear.objects.filter(pk=academic_year_id).first() if academic_year_id else None

            report = FinancialReport.objects.create(
                organization=org,
                created_by=request.user,
                academic_year=ay,
                title=title,
                status='pending_auditor',
            )

            entries = []

            for i in range(len(dates)):
                date        = dates[i]
                category    = categories[i]
                description = descriptions[i]
                amount      = amounts[i]
                

                if not (date and amount):
                    continue

                entry_type    = entry_types[i] if i < len(entry_types) else 'expense'
                income_source = income_sources[i] if i < len(income_sources) else ''
                soc_ay_id     = society_ay_ids[i] if i < len(society_ay_ids) else ''
                product_id    = product_ids[i] if i < len(product_ids) else ''
                variant_id    = variant_ids[i] if i < len(variant_ids) else ''
                student_count   = None
                fee_per_student = None
                product_obj = None
                variant_obj = None

                try:
                    amount = Decimal(str(amount).strip())
                except Exception:
                    amount = Decimal('0')

                try:
                    quantity = int(quantities[i]) if i < len(quantities) and quantities[i] else 1
                except (ValueError, TypeError):
                    quantity = 1
                
                try:
                    raw_unit = unit_prices[i] if i < len(unit_prices) else '0'
                    unit_price = Decimal(raw_unit.strip()) if raw_unit.strip() else None
                except Exception:
                    unit_price = None

                if entry_type == 'income':
                    if income_source == 'society' and soc_ay_id:
                        soc_ay = AcademicYear.objects.filter(pk=soc_ay_id).first()
                        if soc_ay:
                            paid_fees = SocietyFee.objects.filter(
                                organization=org,
                                academic_year=soc_ay,
                                semester=soc_ay.semester,
                                amount_paid__gt=0,
                            )
                            student_count = paid_fees.values('student').distinct().count()
                            fee_per_student = None
                            amount = paid_fees.aggregate(total=Sum('amount_paid'))['total'] or Decimal('0')

                    elif income_source == 'product' and product_id and variant_id:
                        product_obj = Product.objects.filter(pk=product_id, organization=org).first()
                        variant_obj = ProductVariant.objects.filter(pk=variant_id, product=product_obj).first()
                        if variant_obj:
                            amount = variant_obj.price * quantity

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
                    society_semester=None,
                    product=product_obj if income_source == 'product' else None,
                    variant=variant_obj if income_source == 'product' else None,
                    unit_price  = unit_price
                ))

            FinancialReportEntry.objects.bulk_create(entries)

            ReportApprovalLog.objects.create(
                report=report,
                action_by=request.user,
                action='submitted',
                remarks='Report submitted for approval.',
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
            semester=ay.semester,   
            amount_paid__gt=0,
        )
        student_count = paid_fees.values('student').distinct().count()
        total = paid_fees.aggregate(total=Sum('amount_paid'))['total'] or 0

        return JsonResponse({
            'student_count':   student_count,
            'total':           float(total),
            'academic_year':   str(ay),
            'semester':        ay.semester, 
        })
    
class ProductPreviewView(RoleRequireMixin, TemplateView):
    role_required = 'treasurer'

    def get(self, request):
        product_id = request.GET.get('product_id')
        variant_id = request.GET.get('variant_id')
        qty = int(request.GET.get('quantity', 1))

        variant = ProductVariant.objects.filter(
            id=variant_id,
            product_id=product_id
        ).first()

        if not variant:
            return JsonResponse({'error': 'Invalid product/variant'}, status=404)

        unit_price = float(variant.price)
        total = unit_price * qty

        return JsonResponse({
            'unit_price': unit_price,
            'quantity': qty,
            'total': total
        })
