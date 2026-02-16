from django.shortcuts import render
from django.views.generic import TemplateView
# Create your views here.

class HomeTemplateView(TemplateView):
    template_name = 'app/home.html'

class LoginTemplateView(TemplateView):
    template_name = 'app/registration/login.html'