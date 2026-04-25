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
        ("all_program", "All Program"),
    ]
    ORG_CATEGORY = [
        ('academic', 'Academic'),
        ('non_academic', 'Non-Academic'),
        ('performing_arts', 'Performing Arts'),
        ('student_council', 'Student Council'),
        ('student_publication', 'Student Publication'),
    ]
    name = models.CharField(max_length=100)
    logo = models.ImageField(upload_to='organization/logos', blank=True, null=True) 
    program = models.CharField(choices=PROGRAM_CHOICE, blank=True, null=True)
    category = models.CharField(max_length=50, choices=ORG_CATEGORY)
    description = models.TextField()
    balance = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
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

    STATUS_CHOCIES = [
        ('regular', 'Regular'),
        ('irregular', 'Irregular'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    student_id = models.IntegerField()
    program = models.CharField( max_length=20, choices=PROGRAM_CHOICE)
    year = models.IntegerField(choices=YEAR_CHOICES)
    section = models.CharField( max_length=10)
    status = models.CharField(choices=STATUS_CHOCIES)
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
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, null=True, blank=True)
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

class GlobalAnnouncement(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='global_announcements'
    )
    message = models.TextField()
    createdAt = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-createdAt']

    def __str__(self):
        return f"{self.author.get_full_name()} - {self.message[:20]}"

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
    
class FinancialReport(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending_auditor', 'Pending Auditor'),
        ('pending_president', 'Pending President'),
        ('pending_adviser', 'Pending Adviser'),
        ('pending_co_adviser', 'Pending Co-Adviser'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('on_blockchain', 'On Blockchain'),
    ]

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='financial_reports'
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_reports'
    )
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.SET_NULL,
        null=True,
        related_name='financial_reports'
    )
    title = models.CharField(max_length=200)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='draft')

    # Approval chain
    auditor_approved_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='auditor_approved_reports'
    )
    auditor_approved_at = models.DateTimeField(null=True, blank=True)
    auditor_remarks = models.TextField(blank=True, null=True)

    president_approved_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='president_approved_reports'
    )
    president_approved_at = models.DateTimeField(null=True, blank=True)
    president_remarks = models.TextField(blank=True, null=True)

    co_adviser_approved_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='co_adviser_approved_reports'
    )
    co_adviser_approved_at = models.DateTimeField(null=True, blank=True)
    co_adviser_remarks = models.TextField(blank=True, null=True)

    adviser_approved_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='adviser_approved_reports'
    )
    adviser_approved_at = models.DateTimeField(null=True, blank=True)
    adviser_remarks = models.TextField(blank=True, null=True)

    blockchain_hash = models.CharField(max_length=255, blank=True, null=True)
    blockchain_recorded_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.title} - {self.organization}'

    @property
    def total_amount(self):
        return self.entries.aggregate(
            total=models.Sum('amount')
        )['total'] or 0


class FinancialReportEntry(models.Model):
    report = models.ForeignKey(
        FinancialReport,
        on_delete=models.CASCADE,
        related_name='entries'
    )
    ENTRY_TYPE_CHOICES = [
    ('income', 'Income'),
    ('expense', 'Expense'),
    ]

    INCOME_SOURCE_CHOICES = [
        ('society', 'Society Fee'),
        ('product', 'Product Sale'),
        ('other', 'Other Income'),
    ]

    SEMESTER_CHOICES = [
        ('1stSem', '1st Semester'),
        ('2ndSem', '2nd Semester'),
    ]
    date = models.DateField()
    category = models.CharField(max_length=200)
    description = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    order = models.PositiveIntegerField(default=0)
    entry_type = models.CharField(max_length=10, choices=ENTRY_TYPE_CHOICES)
    income_source = models.CharField(max_length=20, choices=INCOME_SOURCE_CHOICES, blank=True, null=True)
    society_student_count = models.PositiveIntegerField(blank=True, null=True)
    society_fee_per_student = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    society_semester = models.CharField(max_length=10, choices=SEMESTER_CHOICES, blank=True, null=True)
    product = models.ForeignKey('Product', null=True, blank=True, on_delete=models.SET_NULL)
    variant = models.ForeignKey('ProductVariant', null=True, blank=True, on_delete=models.SET_NULL)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    receipt_image = models.ImageField(upload_to='financial_reports/receipts/', blank=True, null=True)

    class Meta:
        ordering = ['date', 'order']

    def __str__(self):
        return f'{self.date} - {self.category} - {self.amount}'


class ReportApprovalLog(models.Model):
    ACTION_CHOICES = [
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('blockchain', 'Recorded on Blockchain'),
    ]
    report = models.ForeignKey(
        FinancialReport,
        on_delete=models.CASCADE,
        related_name='approval_logs'
    )
    action_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    remarks = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
    
class Product(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class ProductVariant(models.Model):
    SIZE_CHOICES = [
        ('S', 'Small'),
        ('M', 'Medium'),
        ('L', 'Large'),
        ('XL', 'Extra Large'),
        ('none','N/A'),
    ]

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='variants'
    )

    size = models.CharField(max_length=5, choices=SIZE_CHOICES, null=True, blank=True)
    color = models.CharField(max_length=50, null=True, blank=True)

    price = models.DecimalField(max_digits=10, decimal_places=2)

    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.product.name} - {self.size or ''} {self.color or ''}".strip()
