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
        program = self.data.get('program') or self.initial.get('program')
        if program:
            self.fields['organization'].queryset = Organization.objects.filter(program=program)
        else:
            self.fields['organization'].queryset = Organization.objects.all()

    def clean_student_id(self):
        student_id = self.cleaned_data.get('student_id')
        if Student.objects.filter(student_id=student_id).exists():
            raise forms.ValidationError("A student with this ID already exists.")
        return student_id

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if CustomUser.objects.filter(username=username).exists():
            raise forms.ValidationError("This username is already taken.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already registered.")
        return email

    def save(self, commit=True):
        user = super().save(commit=commit)
        user.role = 'student'
        user.save()

        primary_org = self.cleaned_data['organization']
        program     = self.cleaned_data['program']

        student = Student.objects.create(
            user=user,
            student_id=self.cleaned_data.get('student_id', ''),
            program=program,
            organization=primary_org,
            year=self.cleaned_data['year'],
            section=self.cleaned_data['section'],
        )

        try:
            csg = Organization.objects.get(name="Central Student Government")
            if csg != primary_org:
                student.other_organization.add(csg)
        except Organization.DoesNotExist:
            pass

        return user
    
    
class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = ('first_name', 'last_name' ,'username', 'email', 'role')

