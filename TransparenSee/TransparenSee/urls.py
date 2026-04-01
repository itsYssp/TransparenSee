
from django.contrib import admin
from django.urls import path, include
from accounts.views import CustomLoginView
from django.shortcuts import redirect
from accounts import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('app.urls')),
    path('accounts/', include('accounts.urls')),
    path('get_organizations_by_program/', views.get_organizations_by_program, name='get_organizations_by_program'),
]

