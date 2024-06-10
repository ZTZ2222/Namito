from django.contrib import admin
from django.contrib import messages
from firebase_admin.exceptions import InvalidArgumentError

from namito.advertisement.models import Advertisement, Notification
from namito.advertisement.firebase import send_firebase_notification
from namito.users.models import User


class AdvertisementInline(admin.StackedInline):
    model = Advertisement
    extra = 0



@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'description', 'date', 'image')
    actions = ['send_notification']

    def send_notification(self, request, queryset):
        users_with_tokens = User.objects.filter(
            receive_notifications=True
        ).exclude(fcm_token__isnull=True).exclude(fcm_token__exact='')

        for notification in queryset:
            for user in users_with_tokens:
                try:
                    image_url = request.build_absolute_uri(notification.image.url) if notification.image else None
                    send_firebase_notification(
                        user.fcm_token,
                        notification.title,
                        notification.description,
                        notification.date,
                        image_url
                    )
                except InvalidArgumentError:
                    messages.error(request, f"Ошибка при отправке уведомления пользователю с токеном: {user.fcm_token}")

        self.message_user(request, "Notifications sent successfully")

    send_notification.short_description = "Отправить выбранные уведомления"
