from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    registrationDate = models.DateTimeField(auto_now_add=True)  

    def __str__(self):
        return self.email if self.email else self.username  
