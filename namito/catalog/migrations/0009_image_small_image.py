# Generated by Django 4.2.11 on 2024-04-30 05:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0008_brand_name_en_brand_name_ru_category_name_en_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='image',
            name='small_image',
            field=models.ImageField(blank=True, null=True, upload_to='product_images/'),
        ),
    ]
