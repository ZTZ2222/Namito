# Generated by Django 4.2.11 on 2024-05-13 10:51

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0003_product_active'),
        ('orders', '0002_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ordereditem',
            name='product_variant',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='ordered_items', to='catalog.variant'),
        ),
    ]
