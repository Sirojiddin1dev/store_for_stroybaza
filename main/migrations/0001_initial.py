# Generated by Django 4.2.9 on 2025-01-25 15:31

from django.conf import settings
import django.contrib.auth.models
import django.contrib.auth.validators
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('username', models.CharField(error_messages={'unique': 'A user with that username already exists.'}, help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.', max_length=150, unique=True, validators=[django.contrib.auth.validators.UnicodeUsernameValidator()], verbose_name='username')),
                ('first_name', models.CharField(blank=True, max_length=150, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=150, verbose_name='last name')),
                ('email', models.EmailField(blank=True, max_length=254, verbose_name='email address')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('phone_number', models.CharField(max_length=15, unique=True, verbose_name='Telefon raqami')),
            ],
            options={
                'verbose_name': 'Foydalanuvchi',
                'verbose_name_plural': 'Foydalanuvchilar',
            },
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Nomi')),
            ],
            options={
                'verbose_name': 'Kategoriya',
                'verbose_name_plural': 'Kategoriyalar',
            },
        ),
        migrations.CreateModel(
            name='City',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Nomi')),
            ],
            options={
                'verbose_name': 'Shahar',
                'verbose_name_plural': 'Shaharlar',
            },
        ),
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('pending', 'Kutilmoqda'), ('processing', 'Jarayonda'), ('shipped', "Jo'natildi"), ('delivered', 'Yetkazib berildi'), ('cancelled', 'Bekor qilindi')], default='pending', max_length=20, verbose_name='Holat')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Yaratilgan sana')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Yangilangan sana')),
                ('payment_method', models.CharField(choices=[('cash', 'Naqd pul'), ('click', 'Click'), ('payme', 'Payme')], max_length=20, verbose_name="To'lov usuli")),
                ('delivery_method', models.CharField(choices=[('pickup', "O'zi olib ketish"), ('delivery', 'Yetkazib berish')], max_length=20, verbose_name='Yetkazib berish usuli')),
                ('delivery_address', models.TextField(blank=True, null=True, verbose_name='Yetkazib berish manzili')),
                ('total_amount', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Umumiy summa')),
                ('cashback', models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='Keshbek')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='orders', to=settings.AUTH_USER_MODEL, verbose_name='Foydalanuvchi')),
            ],
            options={
                'verbose_name': 'Buyurtma',
                'verbose_name_plural': 'Buyurtmalar',
            },
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, verbose_name='Nomi')),
                ('description', models.TextField(verbose_name='Tavsif')),
                ('base_price', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Asosiy narx')),
                ('is_available', models.BooleanField(default=True, verbose_name='Mavjud')),
                ('delivery_time', models.PositiveIntegerField(help_text='Yetkazib berish vaqti kunlarda', verbose_name='Yetkazib berish vaqti')),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='products', to='main.category', verbose_name='Kategoriya')),
            ],
            options={
                'verbose_name': 'Mahsulot',
                'verbose_name_plural': 'Mahsulotlar',
            },
        ),
        migrations.CreateModel(
            name='Promotion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200, verbose_name='Sarlavha')),
                ('description', models.TextField(verbose_name='Tavsif')),
                ('image', models.ImageField(upload_to='promotion_images/', verbose_name='Rasm')),
                ('start_date', models.DateTimeField(verbose_name='Boshlanish sanasi')),
                ('end_date', models.DateTimeField(verbose_name='Tugash sanasi')),
                ('is_active', models.BooleanField(default=True, verbose_name='Faol')),
            ],
            options={
                'verbose_name': 'Aksiya',
                'verbose_name_plural': 'Aksiyalar',
            },
        ),
        migrations.CreateModel(
            name='UserAgreement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200, verbose_name='Sarlavha')),
                ('content', models.TextField(verbose_name='Mazmun')),
                ('version', models.CharField(max_length=10, verbose_name='Versiya')),
                ('is_active', models.BooleanField(default=True, verbose_name='Faol')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Yaratilgan sana')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Yangilangan sana')),
            ],
            options={
                'verbose_name': 'Foydalanuvchi shartnomasi',
                'verbose_name_plural': 'Foydalanuvchi shartnomalari',
            },
        ),
        migrations.CreateModel(
            name='ProductVariant',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('color', models.CharField(max_length=50, verbose_name='Rang')),
                ('size', models.CharField(max_length=50, verbose_name="O'lcham")),
                ('price', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Narx')),
                ('in_stock', models.BooleanField(default=True, verbose_name='Omborda mavjud')),
                ('image', models.ImageField(upload_to='product_images/', verbose_name='Rasm')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='variants', to='main.product', verbose_name='Mahsulot')),
            ],
            options={
                'verbose_name': 'Mahsulot varianti',
                'verbose_name_plural': 'Mahsulot variantlari',
            },
        ),
        migrations.CreateModel(
            name='OrderItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.PositiveIntegerField(verbose_name='Miqdori')),
                ('price', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Narx')),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='main.order', verbose_name='Buyurtma')),
                ('product_variant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main.productvariant', verbose_name='Mahsulot varianti')),
            ],
            options={
                'verbose_name': 'Buyurtma elementi',
                'verbose_name_plural': 'Buyurtma elementlari',
            },
        ),
        migrations.AddField(
            model_name='user',
            name='city',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='main.city', verbose_name='Shahar'),
        ),
        migrations.AddField(
            model_name='user',
            name='groups',
            field=models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups'),
        ),
        migrations.AddField(
            model_name='user',
            name='user_permissions',
            field=models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions'),
        ),
        migrations.CreateModel(
            name='Favorite',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main.product', verbose_name='Mahsulot')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='favorites', to=settings.AUTH_USER_MODEL, verbose_name='Foydalanuvchi')),
            ],
            options={
                'verbose_name': 'Sevimli',
                'verbose_name_plural': 'Sevimlilar',
                'unique_together': {('user', 'product')},
            },
        ),
    ]
