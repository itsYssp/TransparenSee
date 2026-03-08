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
    
    
class LogoutTemplate(LogoutView):
    success_url = reverse_lazy('login')
        


