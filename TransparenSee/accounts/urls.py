from django.urls import path
from .views import *

urlpatterns = [
    path('login/', CustomLoginView.as_view(), name='login'),
    path('signup/', CreateOfficerAccount.as_view(), name='signup'),
    path('logout/', LogoutTemplate.as_view(), name='logout')
]
