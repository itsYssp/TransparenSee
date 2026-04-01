from django.db import models
from django.conf import settings
from django.urls import reverse


User = settings.AUTH_USER_MODEL

class Organization(models.Model):
    PROGRAM_CHOICE = [
        ("BSIT", "Bachelor of Science in Information Technology"),
        ("BSCS", "Bachelor of Science in Computer Science"),
        ("BSP", "Bachelor of Science in Psychology"),
        ("BSED-MTH", "Bachelor of Secondary Education - Mathematics "),
        ("BSED-ENG", "Bachelor of Secondary Education - English"),
        ("BSHM", "Bachelor of Science in Hospitality Management"),
        ("BSC", "Bachelor of Science in Criminology"),
        ("BSBA-MM", "Bachelor of Science in Bussiness Administration - Marketing Management"),
        ("BSBA-HR", "Bachelor of Science in Bussiness Admisnustration - Human Resource Management"),
    ]
    ORG_CATEGORY = [
        ('academic', 'Academic'),
        ('non_academic', 'Non-Academic')
    ]
    name = models.CharField(max_length=100)
    logo = models.ImageField(upload_to='organization/logos', blank=True, null=True) 
    program = models.CharField(choices=PROGRAM_CHOICE, blank=True, null=True)
    category = models.CharField(max_length=50, choices=ORG_CATEGORY)
    description = models.TextField()
    society_fee_amount = models.DecimalField(max_digits=10,decimal_places=2,default=0)
    createdAt = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    
    

class Student(models.Model):
    PROGRAM_CHOICE = [
        ("BSIT", "Bachelor of Science in Information Technology"),
        ("BSCS", "Bachelor of Science in Computer Science"),
        ("BSP", "Bachelor of Science in Psychology"),
        ("BSED-MTH", "Bachelor of Secondary Education - Mathematics "),
        ("BSED-ENG", "Bachelor of Secondary Education - English"),
        ("BSHM", "Bachelor of Science in Hospitality Management"),
        ("BSC", "Bachelor of Science in Criminology"),
        ("BSBA-MM", "Bachelor of Science in Bussiness Administration - Marketing Management"),
        ("BSBA-HR", "Bachelor of Science in Bussiness Admisnustration - Human Resource Management"),
    ]
    YEAR_CHOICES = [
    (1, "1st Year"),
    (2, "2nd Year"),
    (3, "3rd Year"),
    (4, "4th Year"),
]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    student_id = models.IntegerField()
    program = models.CharField( max_length=20, choices=PROGRAM_CHOICE)
    year = models.IntegerField(choices=YEAR_CHOICES)
    section = models.CharField( max_length=10)
    organization = models.ForeignKey(Organization, on_delete=models.SET_NULL, blank=True, null=True)

    def __str__(self):
        return f'{self.user.first_name} {self.user.last_name}'
    
class Officer(models.Model):
    COURSE_CHOICE = [
        ("BSIT", "Bachelor of Science in Information Technology"),
        ("BSCS", "Bachelor of Science in Computer Science"),
        ("BSP", "Bachelor of Science in Psychology"),
        ("BSED-MTH", "Bachelor of Secondary Education - Mathematics "),
        ("BSED-ENG", "Bachelor of Secondary Education - English"),
        ("BSHM", "Bachelor of Science in Hospitality Management"),
        ("BSC", "Bachelor of Science in Criminology"),
        ("BSBA-MM", "Bachelor of Science in Bussiness Administration - Marketing Management"),
        ("BSBA-HR", "Bachelor of Science in Bussiness Admisnustration - Human Resource Management"),
    ]
    YEAR_CHOICES = [
    (1, "1st Year"),
    (2, "2nd Year"),
    (3, "3rd Year"),
    (4, "4th Year"),
]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='officer')
    student_id = models.IntegerField()
    program = models.CharField( max_length=20, choices=COURSE_CHOICE)
    year = models.IntegerField(choices=YEAR_CHOICES)
    section = models.CharField( max_length=10)
    organization = models.ForeignKey(Organization, on_delete=models.SET_NULL, blank=True, null=True)
    

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.user.role}"


class Adviser(models.Model):
    organization = models.OneToOneField(Organization, on_delete=models.CASCADE, null=True, blank=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='adviser' )
    employee_id = models.CharField(max_length=20, blank=True, null=True)
    department = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f'{self.user.get_full_name()} - Adviser'
    def get_absolute_url(self):
        return reverse("campus_admin_user_role" )
    
class CampusAdmin(models.Model):
    user = models.OneToOneField( User, on_delete=models.CASCADE, related_name='campus_admin' )
    employee_id = models.CharField(max_length=20, blank=True, null=True)
    department = models.CharField(max_length=100, blank=True, null=True)
    campus = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f'{self.user.get_full_name()} - Campus Admin'

class Head(models.Model):
    DEPARTMENT_CHOICE = [
        ('osas', 'Office of Student Affairs and Service'),
        ('sds', 'Student Development and Services')
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='heads')
    employee_id = models.CharField(max_length=20, blank=True, null=True)
    department = models.CharField(choices=DEPARTMENT_CHOICE ,max_length=50)
    campus = models.CharField(max_length=100, blank=True, null=True)

class GlobalChat(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    createdAt = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user} - {self.message[:20]}"
    
class OrganizationAnnouncement(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='announcements'
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='announcements'
    )
    message = models.TextField()
    createdAt = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-createdAt']

class AcademicYear(models.Model):
    SEMESTER_CHOICES = [
        ('1stSem', '1st Semester'),
        ('2ndSem', '2nd Semester'),
    ]
    academic_year = models.CharField(max_length=20)
    semester = models.CharField(max_length=10, choices=SEMESTER_CHOICES)

    class Meta:
        unique_together = ['academic_year', 'semester']
        ordering = ['-academic_year', 'semester']

    def __str__(self):
        return f'{self.academic_year} - {self.get_semester_display()}'
    

class SocietyFee(models.Model):
    STATUS_CHOICES = [
        ('paid', 'Paid'),
        ('unpaid', 'Unpaid'),
        ('partial', 'Partial'),
    ]
    SEMESTER_CHOICES = [
        ('1stSem', '1st Semester'),
        ('2ndSem', '2nd Semester'),
    ]
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='society_fees'
    )
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='society_fees'
    )
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.CASCADE,
        related_name='society_fees'
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    semester = models.CharField( choices=SEMESTER_CHOICES ,max_length=50)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='unpaid')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['student', 'organization', 'academic_year', 'semester']

    def __str__(self):
        return f'{self.student.get_full_name()} - {self.academic_year}'