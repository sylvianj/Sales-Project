from django.contrib.auth import get_user_model
from django.test import TestCase

from .models import Notification, NotificationChannel, NotificationLog, NotificationRule, NotificationTemplate


class NotificationModelsTest(TestCase):
    def test_notification_models_can_be_created(self):
        User = get_user_model()
        user = User.objects.create_user(username='notifyuser', email='notify@example.com', password='testpass')

        channel = NotificationChannel.objects.create(name='Email Channel', channel_type='email')
        template = NotificationTemplate.objects.create(name='Test Template', subject='Test Subject', body='Hello world')
        rule = NotificationRule.objects.create(name='Test Rule', event='test_event', template=template)
        rule.channels.add(channel)

        notification = Notification.objects.create(
            user=user,
            rule=rule,
            subject='Test Notification',
            message='This is a test notification',
            sent_via='email',
        )

        log = NotificationLog.objects.create(
            notification=notification,
            channel='email',
            status='sent',
            response='OK',
        )

        self.assertEqual(Notification.objects.count(), 1)
        self.assertEqual(NotificationLog.objects.count(), 1)
        self.assertEqual(rule.channels.first(), channel)
        self.assertEqual(log.status, 'sent')
