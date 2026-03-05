from django.db import models
from django.conf import settings

# Create your models here.

class Student(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)

class Organization(models.Model):
    ORG_CATEGORY = [
        ('academic', 'Academic'),
        ('non_academic', 'Non-Academic')
    ]
    name = models.CharField(max_length=100)
    logo = models.ImageField(upload_to='organization/logos', blank=True, null=True) 
    category = models.CharField(max_length=50, choices=ORG_CATEGORY)

    def __str__(self):
        return self.name