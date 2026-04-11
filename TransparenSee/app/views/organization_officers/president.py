from django.views.generic import TemplateView, CreateView, ListView
from django.shortcuts import redirect
from django.contrib import messages
from ...models import *
from ..mixins import *
from django.db.models import Q,Count, Sum
from ...forms import *

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
        recent_approval_log = ReportApprovalLog.objects.filter(report__organization = org).order_by('-created_at')[:5]
        context["society_fee_amount"] = org.society_fee_amount
        context["balance"] = org.balance
        context["pending_financial_reports"] = FinancialReport.objects.filter(organization=org).exclude(status__in=['rejected','approved', 'on_blockchain']).count()
        context["flagged_financial_reports"] = FinancialReport.objects.filter(organization=org, status='rejected').count()
        context["approved_financial_reports"] = FinancialReport.objects.filter(organization=org, status='on_blockchain').count()
        context["recent_approval_logs"] = recent_approval_log
        context['recent_financial_reports'] = FinancialReport.objects.filter(organization=org).exclude(status='rejected').annotate(
            income_count=Count('entries', filter=Q(entries__entry_type='income')),
            expense_count=Count('entries', filter=Q(entries__entry_type='expense')),
        ).order_by('-created_at')[:3]
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
    


class ProductCreateView(RoleRequireMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'app/officer/president/create_product.html'
    role_required = 'president'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['size_choices'] = ProductVariant.SIZE_CHOICES
        return context
        
    def form_valid(self, form):
        product = form.save(commit=False)
        product.organization = self.request.user.officer.organization
        product.save()

        sizes   = self.request.POST.getlist('size[]')
        colors  = self.request.POST.getlist('color[]')
        prices  = self.request.POST.getlist('price[]')

        errors = []

        for i in range(len(prices)):  
            try:
                if not prices[i]:
                    continue

                ProductVariant.objects.create(
                    product=product,
                    size=sizes[i] if i < len(sizes) else None,
                    color=colors[i] if i < len(colors) else None,
                    price=prices[i],
                )

            except Exception as e:
                errors.append(f"Variant {i+1}: {e}")

        if errors:
            product.delete()
            context = self.get_context_data(form=form)
            context['variant_errors'] = errors
            return self.render_to_response(context)

        return redirect('product_list')