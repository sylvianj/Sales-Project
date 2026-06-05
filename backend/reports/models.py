from django.db import models
from django.contrib.auth.models import User

class SavedReport(models.Model):
    REPORT_TYPES = [
        ('sales', 'Sales Report'),
        ('inventory', 'Inventory Report'),
        ('payments', 'Payments Report'),
    ]
    name = models.CharField(max_length=100)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    filters = models.JSONField(default=dict)  # store filter criteria
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    last_run = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.name


class ReportExport(models.Model):
    report = models.ForeignKey(SavedReport, on_delete=models.CASCADE)
    exported_by = models.ForeignKey(User, on_delete=models.CASCADE)
    file = models.FileField(upload_to='reports/')
    format = models.CharField(max_length=10)  # pdf, excel, csv
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.report.name} - {self.created_at}"