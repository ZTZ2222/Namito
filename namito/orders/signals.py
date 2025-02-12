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
    # Инициализация _original_status при создании объекта
    if created:
        instance._original_status = instance.status
        user = instance.user
        if user and user.fcm_token:
            try:
                message_title = 'Заказ создан'
                message_body = (f'Ваш заказ: {instance.order_number} '
                                f'от {instance.created_at.strftime("%d.%m.%Y")} создан.')
                message = messaging.Message(
                    notification=messaging.Notification(title=message_title, body=message_body),
                    token=user.fcm_token
                )

                response = messaging.send(message)
                print('Successfully sent message:', response)
            except Exception as e:
                print('Error sending message:', str(e))
        else:
            print('FCM token is not available for the user.')
    else:
        # Проверка, изменился ли статус
        if instance.status != getattr(instance, '_original_status', None):
            user = instance.user
            if user and user.fcm_token:
                try:
                    if instance.status == 1:
                        message_title = 'Заказ доставлен'
                        message_body = (f'Ваш заказ: {instance.order_number} '
                                        f'от {instance.created_at.strftime("%d.%m.%Y")} успешно доставлен.')
                    elif instance.status == 2:
                        message_title = 'Заказ отменен'
                        message_body = (f'Ваш заказ: {instance.order_number} '
                                        f'от {instance.created_at.strftime("%d.%m.%Y")} был отменен.')
                    elif instance.status == 0:
                        message_title = 'Заказ в процессе'
                        message_body = (f'Ваш заказ: {instance.order_number} '
                                        f'от {instance.created_at.strftime("%d.%m.%Y")} в процессе.')
                    elif instance.status == 3:
                        message_title = 'Заказ отправлен'
                        message_body = (f'Ваш заказ: {instance.order_number} '
                                        f'от {instance.created_at.strftime("%d.%m.%Y")} отправлен.')
                    else:
                        message_title = 'Статус заказа изменен'
                        message_body = (f'Новый статус вашего заказа: {instance.order_number} '
                                        f'от {instance.created_at.strftime("%d.%м.%Y")}: {instance.get_status_display()}.')

                    message = messaging.Message(
                        notification=messaging.Notification(title=message_title, body=message_body),
                        token=user.fcm_token
                    )

                    response = messaging.send(message)
                    print('Successfully sent message:', response)
                except Exception as e:
                    print('Error sending message:', str(e))
            else:
                print('FCM token is not available for the user.')

        # Обновление _original_status
        instance._original_status = instance.status
