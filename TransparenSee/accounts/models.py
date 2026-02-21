from django.db import models
from django.contrib.auth.models import AbstractUser
from app.models import Organization
# Create your models here.

class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('student', 'student'),
        ('officer', 'officer'),
        ('campus admin', 'campus admin'),
    ]
    role = models.CharField( max_length=20, choices=ROLE_CHOICES)
    organization = models.ForeignKey(Organization, on_delete=models.SET_NULL, blank=True, null=True)
    position = models.CharField(max_length=50)
    profile_image = models.ImageField(upload_to="profile_pictures", blank=True, null=True)