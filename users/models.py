from django.contrib.auth.models import AbstractUser
from django.db import models


class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class CustomUser(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        MANAGER = "MANAGER", "Manager"
        USER = "USER", "User"

    role = models.CharField(max_length=10, choices=Role.choices, default=Role.USER)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name="users")
    dob_id = models.CharField(max_length=20, unique=True, verbose_name="DOB ID")
    
    def is_admin(self):
        return self.role == self.Role.ADMIN

    def is_manager(self):
        return self.role == self.Role.MANAGER

    def __str__(self):
        if self.first_name:
            # return f"{self.username}: {self.first_name}"
            return f"{self.first_name}"
        return self.username
    



class PrimarySetting(models.Model):
    auto_approve = models.BooleanField(default=False)
