from django.db import models
from django.contrib.auth.models import User
from django.db import models
from django.contrib.auth.models import User

class AuditLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    endpoint = models.CharField(max_length=255)
    method = models.CharField(max_length=10)
    query_params = models.TextField(blank=True)
    body = models.TextField(blank=True)

    def __str__(self):
        return f"{self.timestamp} - {self.user.username} accessed {self.endpoint}"

class FileAccess(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    resource = models.CharField(max_length=255)
    can_read = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {self.resource} ({'read' if self.can_read else 'no read'})"

# Create your models here.
