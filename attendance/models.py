from django.db import models
from django.conf import settings

class Attendance(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    check_in = models.DateTimeField(auto_now_add=True)
    check_out = models.DateTimeField(null=True, blank=True)
    date = models.DateField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'date']
    class Meta:
        ordering = ['-date', '-check_in']
        verbose_name_plural = 'Attendance Records'

    def __str__(self):
        return f"{self.user.username} - {self.date}"