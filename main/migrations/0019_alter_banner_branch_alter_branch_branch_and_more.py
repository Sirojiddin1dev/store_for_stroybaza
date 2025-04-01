# Generated by Django 4.2.9 on 2025-02-17 18:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0018_branch_branch_product_branch_socialmedia_branch_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='banner',
            name='branch',
            field=models.IntegerField(choices=[(0, 'Stroy baza'), (1, 'Giaz mebel'), (2, 'Gold Klinker')], default=0),
        ),
        migrations.AlterField(
            model_name='branch',
            name='branch',
            field=models.IntegerField(choices=[(0, 'Stroy baza'), (1, 'Giaz mebel'), (2, 'Gold Klinker')], default=0),
        ),
        migrations.AlterField(
            model_name='category',
            name='branch',
            field=models.IntegerField(choices=[(0, 'Stroy baza'), (1, 'Giaz mebel'), (2, 'Gold Klinker')], default=0),
        ),
        migrations.AlterField(
            model_name='product',
            name='branch',
            field=models.IntegerField(choices=[(0, 'Stroy baza'), (1, 'Giaz mebel'), (2, 'Gold Klinker')], default=0),
        ),
        migrations.AlterField(
            model_name='socialmedia',
            name='branch',
            field=models.IntegerField(choices=[(0, 'Stroy baza'), (1, 'Giaz mebel'), (2, 'Gold Klinker')], default=0),
        ),
        migrations.AlterField(
            model_name='support',
            name='branch',
            field=models.IntegerField(choices=[(0, 'Stroy baza'), (1, 'Giaz mebel'), (2, 'Gold Klinker')], default=0),
        ),
        migrations.AlterField(
            model_name='useragreement',
            name='branch',
            field=models.IntegerField(choices=[(0, 'Stroy baza'), (1, 'Giaz mebel'), (2, 'Gold Klinker')], default=0),
        ),
    ]
