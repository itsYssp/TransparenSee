from .forms import CustomUserCreationForm
from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.contrib.auth.views import LoginView, LogoutView
from app.models import Organization
from .models import CustomUser
from django.shortcuts import redirect
from django.http import JsonResponse

def get_organizations_by_program(request):
        program = request.GET.get('program')
        orgs = Organization.objects.filter(program=program)
        data = [{'id': o.id, 'name': o.name} for o in orgs]
        return JsonResponse(data, safe=False)
    

class CustomUserCreationView(CreateView):
    form_class = CustomUserCreationForm
    template_name = 'registration/signup.html'
    success_url = reverse_lazy('login')

class CustomLoginView(LoginView):
    template_name = 'registration/login.html'
    
    def dispatch(self, request, *args, **kwargs):
        user = request.user
        if user.is_authenticated:
            return redirect(reverse_lazy('home'))
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["user_count"] = CustomUser.objects.count()
        context["organization_count"] = Organization.objects.count()
        return context
    
class LogoutTemplate(LogoutView):
    success_url = reverse_lazy('login')
        


