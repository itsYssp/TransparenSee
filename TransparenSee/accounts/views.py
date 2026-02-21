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
        print(f"DEBUG: Logged in user: {user.username}, role: {user.role}")  # <-- see the role

        if user.role == 'officer':
            print("DEBUG: Redirecting to officer dashboard")  # <-- check direction
            return reverse_lazy('officer_dashboard')
        elif user.role == 'student':
            print("DEBUG: Redirecting to student dashboard")  # <-- check direction
            return reverse_lazy('student_dashboard')
        else:
            print("DEBUG: Redirecting to home")  # <-- fallback
            return reverse_lazy('home')
    
class LogoutTemplate(LogoutView):
    success_url = reverse_lazy('login')
        


