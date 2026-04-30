from django import forms
from django.contrib.auth.forms import UserCreationForm
from accounts.models import CustomUser
from .models import *
from django import forms
from django.forms import inlineformset_factory
from .models import Product, ProductVariant


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
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2','role' ]

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = self.cleaned_data['role']
        if commit:
            user.save()
            Adviser.objects.create(
                user=user,
                organization = self.cleaned_data.get('organization'),
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

class GlobalAnnouncementForm(forms.ModelForm):
    class Meta:
        model = GlobalAnnouncement
        fields = ['message']

class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['student_id','year', 'program', 'section']

class OfficerForm(forms.ModelForm):
    class Meta:
        model = Officer
        fields = ['student_id','year', 'program', 'section','signature'] 

class OrganizationForm(forms.ModelForm):
    program = forms.ChoiceField(choices=Organization.PROGRAM_CHOICE,required=True)
    category = forms.ChoiceField(choices=Organization.ORG_CATEGORY, required=True)
    class Meta:
        model = Organization
        fields = ['name', 'logo','description', 'program', 'category']


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description', 'is_active']


class AccomplishmentReportForm(forms.ModelForm):
    class Meta:
        model = AccomplishmentReport
        fields = ['title', 'desciption', 'report_file']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['title'].widget.attrs.update({
            'class': 'input input-bordered w-full bg-white',
            'placeholder': 'Enter report title',
        })
        self.fields['desciption'].widget.attrs.update({
            'class': 'textarea textarea-bordered w-full min-h-28 bg-white',
            'placeholder': 'Summarize the accomplishment report',
        })
        self.fields['report_file'].widget.attrs.update({
            'class': 'file-input file-input-bordered w-full bg-white',
            'accept': 'application/pdf,.pdf',
        })
        self.fields['report_file'].required = True
        self.fields['report_file'].label = 'Accomplishment Report PDF'

    def clean_report_file(self):
        report_file = self.cleaned_data.get('report_file')
        if not report_file:
            raise forms.ValidationError('Please upload a PDF file.')

        filename = report_file.name.lower()
        content_type = getattr(report_file, 'content_type', '')
        if not filename.endswith('.pdf') or (content_type and content_type != 'application/pdf'):
            raise forms.ValidationError('Only PDF files are allowed.')

        return report_file

from django import forms
from .models import AcademicYear


PERIOD_TYPE_CHOICES = [
    ("monthly",   "Monthly"),
    ("semestral", "Semestral"),
    ("yearly",    "Yearly"),
    ("event",     "Specific Event / Date Range"),
]

SEMESTER_CHOICES = [
    ("1stSem", "1st Semester"),
    ("2ndSem", "2nd Semester"),
]

MONTH_CHOICES = [(i, name) for i, name in {
    1:"January", 2:"February", 3:"March", 4:"April",
    5:"May", 6:"June", 7:"July", 8:"August",
    9:"September", 10:"October", 11:"November", 12:"December",
}.items()]


class FinancialStatementForm(forms.Form):
    report_title      = forms.CharField(max_length=200, required=False)
    period_type       = forms.ChoiceField(choices=PERIOD_TYPE_CHOICES)
    academic_year     = forms.ModelChoiceField(
        queryset=AcademicYear.objects.all(), required=False
    )
    month             = forms.ChoiceField(choices=MONTH_CHOICES, required=False)
    semester          = forms.ChoiceField(choices=SEMESTER_CHOICES, required=False)
    start_date        = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))
    end_date          = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))
    record_blockchain = forms.BooleanField(required=False)

    def clean(self):
        cleaned = super().clean()
        period_type = cleaned.get("period_type")

        if period_type == "monthly":
            if not cleaned.get("academic_year"):
                self.add_error("academic_year", "Required for monthly reports.")
            if not cleaned.get("month"):
                self.add_error("month", "Required for monthly reports.")

        elif period_type == "semestral":
            if not cleaned.get("academic_year"):
                self.add_error("academic_year", "Required for semestral reports.")
            if not cleaned.get("semester"):
                self.add_error("semester", "Required for semestral reports.")

        elif period_type == "yearly":
            if not cleaned.get("academic_year"):
                self.add_error("academic_year", "Required for yearly reports.")

        elif period_type == "event":
            if not cleaned.get("start_date"):
                self.add_error("start_date", "Required for event-based reports.")
            if not cleaned.get("end_date"):
                self.add_error("end_date", "Required for event-based reports.")
            if cleaned.get("start_date") and cleaned.get("end_date"):
                if cleaned["start_date"] > cleaned["end_date"]:
                    self.add_error("end_date", "End date must be after start date.")

        return cleaned
