from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import TemplateView

class HomeTemplateView(TemplateView):
    template_name = 'app/home.html'
    def dispatch(self, request, *args, **kwargs):
        user = request.user
        if user.is_authenticated:
            if user.is_superuser:
                return redirect(reverse_lazy('superadmin_dashboard'))
            elif user.role == 'treasurer':
                return redirect(reverse_lazy('treasurer_dashboard'))
            elif user.role == 'auditor':
                return redirect(reverse_lazy('auditor_dashboard'))
            elif user.role == 'adviser':
                return redirect(reverse_lazy('adviser_dashboard'))
            elif user.role == 'co_adviser':
                return redirect(reverse_lazy('adviser_dashboard'))
            elif user.role == 'president':
                return redirect(reverse_lazy('president_dashboard'))
            elif user.role == 'campus_admin':
                return redirect(reverse_lazy('campus_admin_dashboard'))
            elif user.role == 'head':
                return redirect(reverse_lazy('head_dashboard'))
            elif user.role == 'student':
                return redirect(reverse_lazy('student_dashboard'))
        return redirect(reverse_lazy('login'))
        

class LandingPage(TemplateView):
    template_name = 'app/landing_page.html'
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(reverse_lazy('home'))
        return super().dispatch(request, *args, **kwargs)