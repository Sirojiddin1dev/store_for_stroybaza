# Generated by Django 4.2.9 on 2025-02-10 16:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0014_alter_order_delivery_method_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='SocialMedia',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('instagram', models.CharField(max_length=500, verbose_name='Instagram havolangiz')),
                ('telegram', models.CharField(max_length=500, verbose_name='Telegram havolangiz')),
                ('youtube', models.CharField(max_length=500, verbose_name='Youtube havolangiz')),
            ],
        ),
        migrations.RemoveField(
            model_name='support',
            name='description_en',
        ),
        migrations.RemoveField(
            model_name='support',
            name='description_ru',
        ),
        migrations.RemoveField(
            model_name='support',
            name='description_uz',
        ),
    ]
