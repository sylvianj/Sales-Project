from django.db import models
from django.contrib.auth.models import User

class NotificationChannel(models.Model):
    CHANNEL_TYPES = [
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('push', 'Push Notification'),
    ]
    name = models.CharField(max_length=100)
    channel_type = models.CharField(max_length=20, choices=CHANNEL_TYPES)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class NotificationTemplate(models.Model):
    name = models.CharField(max_length=100)
    subject = models.CharField(max_length=200, blank=True)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class NotificationRule(models.Model):
    name = models.CharField(max_length=100)
    event = models.CharField(max_length=100)  # e.g., 'low_stock', 'new_sale'
    template = models.ForeignKey(NotificationTemplate, on_delete=models.CASCADE)
    channels = models.ManyToManyField(NotificationChannel)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    rule = models.ForeignKey(NotificationRule, on_delete=models.CASCADE)
    subject = models.CharField(max_length=200)
    message = models.TextField()
    sent_via = models.CharField(max_length=20)  # email, sms, push
    sent_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"Notification to {self.user} - {self.sent_at}"


class NotificationLog(models.Model):
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE)
    channel = models.CharField(max_length=20)
    status = models.CharField(max_length=20)  # sent, failed, pending
    response = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Log for {self.notification} via {self.channel}"