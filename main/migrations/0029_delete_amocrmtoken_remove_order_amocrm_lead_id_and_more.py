# Generated by Django 5.1.2 on 2025-03-28 15:19

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0028_alter_order_status_delete_paymeorder'),
    ]

    operations = [
        migrations.DeleteModel(
            name='AmoCRMToken',
        ),
        migrations.RemoveField(
            model_name='order',
            name='amocrm_lead_id',
        ),
        migrations.RemoveField(
            model_name='order',
            name='amocrm_status',
        ),
    ]
