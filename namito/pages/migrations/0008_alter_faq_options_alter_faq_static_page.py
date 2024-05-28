# Generated by Django 4.2.11 on 2024-05-28 08:51

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0007_faq'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='faq',
            options={'verbose_name': 'Вопрос', 'verbose_name_plural': 'Вопросы'},
        ),
        migrations.AlterField(
            model_name='faq',
            name='static_page',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='faqs', to='pages.staticpage'),
        ),
    ]
