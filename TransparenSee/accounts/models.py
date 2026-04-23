from django.db import models
from django.urls import reverse
from django.contrib.auth.models import AbstractUser,  BaseUserManager
from app.models import Organization
# Create your models here.

class CustomUserManager(BaseUserManager):

    def create_user(self, username, email, first_name, last_name, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")

        email = self.normalize_email(email)

        user = self.model(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            **extra_fields
        )

        user.set_password(password)
        user.save(using=self._db)
        return user


    def create_superuser(self, username, email, first_name, last_name, password=None, **extra_fields):

        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'admin')

        return self.create_user(
            username,
            email,
            first_name,
            last_name,
            password,
            **extra_fields
        )


class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('campus_admin', 'Campus Admin'),
        ('adviser', 'Adviser'),
        ('co_adviser', 'Co-Adviser'),
        ('treasurer', 'Treasurer'),
        ('auditor', 'Auditor'),
        ('president', 'President'),
        ('secretary', 'Secretary'),
        ('student', 'Student'),
        ('head', 'Head')
    ]
    
    middle_name = models.CharField(max_length=50)
    role = models.CharField( max_length=20, choices=ROLE_CHOICES)
    profile_image = models.ImageField(upload_to="profile_pictures", blank=True, null=True)
    REQUIRED_FIELDS = ['email', 'first_name', 'last_name']
    objects = CustomUserManager()


    