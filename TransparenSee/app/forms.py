from django import forms
from django.contrib.auth.forms import UserCreationForm
from accounts.models import CustomUser
from .models import *



class OfficerCreationForm(UserCreationForm):
    student_id = forms.CharField(max_length=20)
    program = forms.ChoiceField(choices=Student.PROGRAM_CHOICE, required=False)
    year = forms.IntegerField(required=True)
    section = forms.CharField(max_length=10, required=True)

    organization = forms.ModelChoiceField(
        queryset=Organization.objects.all(),
        required=True,
        empty_label="-- Select Organization --"
    )

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2', 'role']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = self.cleaned_data['role']
        if commit:
            user.save()
            Officer.objects.create(
                user=user,
                student_id = self.cleaned_data.get('student_id', ''),
                organization = self.cleaned_data.get('organization', ''),
                program=self.cleaned_data.get('program', ''),
                year=self.cleaned_data['year'],
                section=self.cleaned_data['section'],
            )
        return user
    
class AdviserCreationForm(UserCreationForm):
    employee_id = forms.CharField(max_length=20, required=False)
    department = forms.CharField(max_length=100, required=False)

    organization = forms.ModelChoiceField(
        queryset=Organization.objects.all(),
        required=True,
        empty_label="-- Select Organization --"
    )

    class Meta:

        model = CustomUser
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2', ]

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'adviser'
        
        if commit:
            user.save()
            Adviser.objects.create(
                user=user,
                organization = self.cleaned_data.get('organization', ''),
                employee_id=self.cleaned_data.get('employee_id', ''),
                department=self.cleaned_data.get('department', ''),
            )
        return user

class CampusAdminCreationForm(UserCreationForm):
    employee_id = forms.CharField(max_length=20, required=False)
    department = forms.CharField(max_length=100, required=False)
    campus = forms.CharField(max_length=100, required=False)

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'campus_admin'
        if commit:
            user.save()
            CampusAdmin.objects.create(
                user=user,
                employee_id=self.cleaned_data.get('employee_id', ''),
                department=self.cleaned_data.get('department', ''),
                campus=self.cleaned_data.get('campus', ''),
            )
        return user

class HeadCreationForm(UserCreationForm):
    employee_id = forms.CharField(max_length=20, required=False)
    department = forms.ChoiceField(choices=Head.DEPARTMENT_CHOICE, required=True)
    campus = forms.CharField(max_length=100, required=False)

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'head'
        if commit:
            user.save()
            Head.objects.create(
                user=user,
                employee_id=self.cleaned_data.get('employee_id', ''),
                department=self.cleaned_data.get('department', ''),
                campus=self.cleaned_data.get('campus', ''),
            )
        return user

class GlobalChatForm(forms.ModelForm):
    class Meta:
        model = GlobalChat
        fields = ['message']

class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = OrganizationAnnouncement
        fields = ['message']

class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['year', 'program', 'section']

class OrganizationForm(forms.ModelForm):
    program = forms.ChoiceField(choices=Organization.PROGRAM_CHOICE,required=True)
    category = forms.ChoiceField(choices=Organization.ORG_CATEGORY, required=True)
    class Meta:
        model = Organization
        fields = ['name', 'logo','description', 'program', 'category']
