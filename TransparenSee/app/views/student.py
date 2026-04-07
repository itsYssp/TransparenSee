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
from django.db.models import Sum, Q

class StudentDashboardView(RoleRequireMixin, TemplateView):
    template_name = "app/student/dashboard.html"
    role_required = 'student'

    load_dotenv(override=True)
    SEPOLIA_URL      = os.getenv("SEPOLIA_URL")
    CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS")
    web3 = Web3(Web3.HTTPProvider(SEPOLIA_URL))
    web3.middleware_onion.inject(geth_poa_middleware, layer=0)
    contract = web3.eth.contract(address=CONTRACT_ADDRESS, abi=contract_abi)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        org = None
        if hasattr(user, 'student'):
            org = user.student.organization

        # Fetch blockchain transactions
        try:
            transactions = self.contract.functions.getTransactions().call()
        except Exception as e:
            transactions = []
            print("Error fetching transactions:", e)

        tx_list = []
        for t in transactions:
            tx_list.append({
                "organization": t[0],
                "amount":       t[1] / 100,   # convert cents back to pesos
                "sender":       t[2],
                "timestamp":    datetime.fromtimestamp(t[3]).strftime('%Y-%m-%d %H:%M:%S'),
                "report_hash":  t[4],
                "title":        t[5],
            })

        # Filter to only show this student's organization transactions
        if org:
            org_tx_list = [t for t in tx_list if t['organization'] == org.name]
        else:
            org_tx_list = []

        context['transactions'] = org_tx_list
        context['tx_count']     = len(org_tx_list)

        # Financial reports — only approved/on_blockchain visible to students
        if org:
            context['financial_reports'] = FinancialReport.objects.filter(
                organization=org,
                status__in=['approved', 'on_blockchain']
            ).annotate(
                total_income=Sum('entries__amount', filter=Q(entries__entry_type='income')),
                total_expense=Sum('entries__amount', filter=Q(entries__entry_type='expense')),
            ).order_by('-created_at')
        else:
            context['financial_reports'] = FinancialReport.objects.none()

        context['active_tab'] = self.request.GET.get('type', 'financial')
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