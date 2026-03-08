from django import forms
from django.contrib.auth.forms import UserCreationForm
from accounts.models import CustomUser
from .models import Organization


class CampusAdminCreationForm(UserCreationForm):

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'campus_admin'
        if commit:
            user.save()
        return user


class AdviserCreationForm(UserCreationForm):
    organization = forms.ModelChoiceField(
        queryset=Organization.objects.none(),  
        required=True ,
        empty_label="-- Select Organization --"
    )
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2', 'organization']


    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'adviser'
        if commit:
            user.save()
        return user
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    
        if self.instance and self.instance.pk:
            self.fields['organization'].queryset = Organization.objects.exclude(
                customuser__isnull=False
            ) | Organization.objects.filter(pk=self.instance.organization_id)

class UpdateAdviserForm(forms.ModelForm):
    organization = forms.ModelChoiceField(
        queryset=Organization.objects.all(),
        required=True,
        empty_label="-- Select Organization --"
    )

    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'username', 'email', 'organization']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Exclude organizations already assigned to another adviser
        # BUT include the current adviser's organization
        if self.instance and self.instance.pk:
            self.fields['organization'].queryset = Organization.objects.exclude(
                customuser__isnull=False
            ) | Organization.objects.filter(pk=self.instance.organization_id)

class OfficerCreationForm(UserCreationForm):

    organization = forms.ModelChoiceField(
        queryset=Organization.objects.all(),
        required=True ,
        empty_label="-- Select Organization --"
    )

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2', 'organization']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'officer'
        if commit:
            user.save()
        return user