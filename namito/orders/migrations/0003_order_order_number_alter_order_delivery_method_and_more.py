# Generated by Django 4.2.11 on 2024-04-29 04:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0002_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='order_number',
            field=models.CharField(blank=True, max_length=20, null=True, unique=True),
        ),
        migrations.AlterField(
            model_name='order',
            name='delivery_method',
            field=models.CharField(choices=[('курьером', 'Курьером'), ('самовызов', 'Самовывоз')], default='курьером', max_length=20),
        ),
        migrations.AlterField(
            model_name='order',
            name='payment_method',
            field=models.CharField(choices=[('наличкой', 'Наличкой'), ('картой', 'Картой')], default='картой', max_length=20),
        ),
        migrations.AlterField(
            model_name='order',
            name='payment_status',
            field=models.IntegerField(choices=[(0, 'Не оплачено'), (1, 'Платеж в процессе'), (2, 'Оплачено')], default='Платеж в процессе'),
        ),
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.IntegerField(choices=[(0, 'В процессе'), (1, 'Доставлено'), (3, 'Доставка отменена')], default='В процессе'),
        ),
    ]
