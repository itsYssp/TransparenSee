from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django import forms
from .models import CustomUser
from app.models import Organization, Student

class CustomUserCreationForm(UserCreationForm):
    student_id = forms.IntegerField(required=True)
    program = forms.ChoiceField(choices=Student.PROGRAM_CHOICE, required=False)
    organization = forms.ModelChoiceField(
        queryset=Organization.objects.none(), 
        required=True
    )
    year = forms.IntegerField(required=True)
    section = forms.CharField(max_length=10, required=True)

    class Meta:  
        model = CustomUser
        fields = ('first_name', 'last_name', 'username', 'email', 'password1', 'password2')

    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # If the form is bound and 'program' is selected
        program = self.data.get('program') or self.initial.get('program')
        if program:
            self.fields['organization'].queryset = Organization.objects.filter(program=program)
        else:
            self.fields['organization'].queryset = Organization.objects.all()

    def save(self, commit=True):
        user = super().save(commit=commit)
        user.role = 'student'
        user.save()

        Student.objects.create(
            user=user,
            student_id=self.cleaned_data.get('student_id', ''),
            program=self.cleaned_data['program'],
            organization=self.cleaned_data['organization'],
            year=self.cleaned_data['year'],
            section=self.cleaned_data['section'],
        )
        return user
class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = ('first_name', 'last_name' ,'username', 'email', 'role')

