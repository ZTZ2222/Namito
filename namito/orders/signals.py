from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver

from .models import Order

from firebase_admin import messaging


@receiver(pre_save, sender=Order)
def track_status_change(sender, instance, **kwargs):
    if instance.pk:
        original_order = Order.objects.get(pk=instance.pk)
        instance._original_status = original_order.status


@receiver(post_save, sender=Order)
def send_order_status_notification(sender, instance, created, **kwargs):
    if not created and instance.status != getattr(instance, '_original_status', None):
        if instance.status == 1:
            message_title = 'Заказ доставлен'
            message_body = 'Ваш заказ успешно доставлен.'
        elif instance.status == 2:
            message_title = 'Заказ отменен'
            message_body = 'Ваш заказ был отменен.'
        elif instance.status == 0:
            message_title = 'Заказ в процессе'
            message_body = 'Ваш заказ в процессе.'
        else:
            message_title = 'Статус заказа изменен'
            message_body = f'Новый статус вашего заказа: {instance.get_status_display()}.'

        if instance.user.fcm_token:
            message = messaging.Message(
                notification=messaging.Notification(title=message_title, body=message_body),
                token=instance.user.fcm_token
            )

            try:
                response = messaging.send(message)
                print('Successfully sent message:', response)
            except Exception as e:
                print('Error sending message:', str(e))
        else:
            print('FCM token is not available for the user.')
