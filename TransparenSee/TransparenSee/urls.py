
from django.contrib import admin
from django.urls import path, include
from accounts.views import CustomLoginView
from django.shortcuts import redirect

# Redirect root URL to login
def redirect_to_login(request):
    return redirect('login')  # 'login' is the name of your login URL

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', redirect_to_login),
    path('', include('app.urls')),
    path('accounts/', include('accounts.urls')),
    
]

