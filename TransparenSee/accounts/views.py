from .forms import CustomUserCreationForm
from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.contrib.auth.views import LoginView, LogoutView
from app.models import Organization

class CreateOfficerAccount(CreateView):
    form_class = CustomUserCreationForm
    template_name = 'registration/signup.html'
    success_url = reverse_lazy('login')

class CustomLoginView(LoginView):
    template_name = 'registration/login.html'
    def get_success_url(self):
        user = self.request.user
        if user.is_superuser:
            return reverse_lazy('superadmin_dashboard')
        if user.role == 'treasurer':
            return reverse_lazy('treasurer_dashboard')
        if user.role == 'auditor':
            return reverse_lazy('auditor_dashboard')
        elif user.role == 'adviser':
            return reverse_lazy('adviser_dashboard')
        elif user.role == 'campus_admin':
            return reverse_lazy('campus_admin_dashboard') 
        elif user.role == 'student':  
            return reverse_lazy('student_dashboard')
        else:
            print("DEBUG: Redirecting to home") 
            return reverse_lazy('home')
    
class LogoutTemplate(LogoutView):
    success_url = reverse_lazy('login')
        


