from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django import forms
from .models import CustomUser
from app.models import Organization

class CustomUserCreationForm(UserCreationForm):
    organization = forms.ModelChoiceField(
        queryset=Organization.objects.all(),  # make sure this is not empty
        required=True,
        empty_label="-- Select Organization --"
    )
    class Meta(UserCreationForm):
        model= CustomUser
        fields = ('first_name', 'last_name' ,'username', 'email', 'organization', 'position', 'role')

class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = ('first_name', 'last_name' ,'username', 'email', 'organization', 'position', 'role')
