from django.db import models, transaction
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from decimal import Decimal
from django.core.exceptions import ValidationError
from datetime import timedelta
from django.utils import timezone
from django.db.models import Sum, F
# from .amocrm import send_order_to_amocrm
import logging
from django.utils.timezone import now
logger = logging.getLogger(__name__)


class User(AbstractUser):
    phone_number = models.CharField(_("Telefon raqami"), max_length=15, unique=True)
    is_phone_verified = models.BooleanField(_("Telefon tasdiqlangan"), default=False)
    verification_code = models.CharField(_("Tasdiqlash kodi"), max_length=6, blank=True, null=True)
    cashback_balance = models.DecimalField(_("Cashback balansi"), max_digits=10, decimal_places=2, default=0)
    city = models.ForeignKey('City', on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("Shahar"))
    verification_code_attempts = models.IntegerField(_("Tasdiqlash kodi yuborish urinishlari"), default=0)
    last_verification_attempt = models.DateTimeField(_("Oxirgi tasdiqlash urinishi vaqti"), null=True, blank=True)


    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['phone_number']

    def __str__(self):
        return self.username or self.phone_number

    def add_cashback(self, amount):
        self.cashback_balance += Decimal(amount)
        self.save()

    def use_cashback(self, amount):
        if self.cashback_balance >= amount:
            self.cashback_balance -= Decimal(amount)
            self.save()
            return True
        return False

    class Meta:
        verbose_name = _("Foydalanuvchi")
        verbose_name_plural = _("Foydalanuvchilar")


class Region(models.Model):
    name_uz = models.CharField(_("Nomi (O'zbek)"), max_length=100)
    name_ru = models.CharField(_("Название (Русский)"), max_length=100)
    name_en = models.CharField(_("Name (English)"), max_length=100)

    def __str__(self):
        return self.name_uz


class City(models.Model):
    region = models.ForeignKey(Region, on_delete=models.CASCADE, related_name='cities')
    name_uz = models.CharField(_("Nomi (O'zbek)"), max_length=100)
    name_ru = models.CharField(_("Название (Русский)"), max_length=100)
    name_en = models.CharField(_("Name (English)"), max_length=100)

    def __str__(self):
        return self.name_uz


class Category(models.Model):
    BRANCH_CHOICES = (
        (0, 'Stroy baza'),
        (1, 'Giaz mebel'),
        (2, 'Gold Klinker'),
    )
    branch = models.IntegerField(default=0, choices=BRANCH_CHOICES)
    name_uz = models.CharField(_("Nomi (O'zbek)"), max_length=100)
    name_ru = models.CharField(_("Название (Русский)"), max_length=100)
    name_en = models.CharField(_("Name (English)"), max_length=100)

    def __str__(self):
        return self.name_uz

    class Meta:
        verbose_name = _("Kategoriya")
        verbose_name_plural = _("Kategoriyalar")


class Product(models.Model):
    BRANCH_CHOICES = (
        (0, 'Stroy baza'),
        (1, 'Giaz mebel'),
        (2, 'Gold Klinker'),
    )
    branch = models.IntegerField(default=0, choices=BRANCH_CHOICES)
    name_uz = models.CharField(_("Nomi (O'zbek)"), max_length=200)
    name_ru = models.CharField(_("Название (Русский)"), max_length=200)
    name_en = models.CharField(_("Name (English)"), max_length=200)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    is_available = models.BooleanField(_("Mavjud"), default=True)
    description_uz = models.TextField(_("Tavsif (O'zbek)"), blank=True)
    description_ru = models.TextField(_("Описание (Русский)"), blank=True)
    description_en = models.TextField(_("Description (English)"), blank=True)
    image = models.ImageField(_("Rasm"), upload_to='products/')
    views = models.IntegerField(default=0)
    ikpu = models.CharField(_("ikpu raqami"), max_length=100)
    units_id = models.IntegerField(_("o'lchov birligi raqami"), default=1377058)
    units_uz = models.CharField(_("o'lchov birligi nomi (O'zbek)"), max_length=100, default="dona")
    units_en = models.CharField(_("o'lchov birligi nomi (Русский)"), max_length=100, default="dona")
    units_ru = models.CharField(_("o'lchov birligi nomi (English)"), max_length=100, default="dona")

    def __str__(self):
        return self.name_uz

    class Meta:
        verbose_name = _("Mahsulot")
        verbose_name_plural = _("Mahsulotlar")

class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants', verbose_name=_("Mahsulot"))
    color_uz = models.CharField(_("Rang (O'zbek)"), max_length=50, null=True, blank=True)
    color_ru = models.CharField(_("Цвет (Русский)"), max_length=50, null=True, blank=True)
    color_en = models.CharField(_("Color (English)"), max_length=50, null=True, blank=True)
    size_uz = models.CharField(_("O'lcham (O'zbek)"), max_length=50, null=True, blank=True)
    size_ru = models.CharField(_("Размер (Русский)"), max_length=50, null=True, blank=True)
    size_en = models.CharField(_("Size (English)"), max_length=50, null=True, blank=True)
    price = models.DecimalField(_("Narx"), max_digits=10, decimal_places=2)
    is_available = models.BooleanField(_("Mavjud"), default=True)
    image = models.ImageField(_("Rasm"), upload_to='product_images/', null=True, blank=True)
    monthly_payment_3 = models.DecimalField(_("3 oylik to'lov"), max_digits=10, decimal_places=2, editable=False)
    monthly_payment_6 = models.DecimalField(_("6 oylik to'lov"), max_digits=10, decimal_places=2, editable=False)
    monthly_payment_12 = models.DecimalField(_("12 oylik to'lov"), max_digits=10, decimal_places=2, editable=False)
    monthly_payment_24 = models.DecimalField(_("24 oylik to'lov"), max_digits=10, decimal_places=2, editable=False)

    def save(self, *args, **kwargs):
        self.monthly_payment_3 = self.price / Decimal(3)
        self.monthly_payment_6 = self.price / Decimal(6)
        self.monthly_payment_12 = self.price / Decimal(12)
        self.monthly_payment_24 = self.price / Decimal(24)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.name_uz} - {self.color_uz} - {self.size_uz}"

    class Meta:
        verbose_name = _("Mahsulot varianti")
        verbose_name_plural = _("Mahsulot variantlari")


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', _('Kutilmoqda')),
        ('in_payment', _('To\'lov jarayonida')),
        ('processing', _('Jarayonda')),
        ('shipped', _('Jo\'natildi')),
        ('delivered', _('Yetkazib berildi')),
        ('cancelled', _('Bekor qilindi')),
    ]

    PAYMENT_CHOICES = [
        ('cash', _('Naqd pul')),
        ('click', _('Click')),
        ('payme', _('Payme')),
        ('installments_payment', _('Bo\'lib to\'lash')),
    ]

    DELIVERY_CHOICES = [
        ('pickup', _('O\'zi olib ketish')),
        ('delivery', _('Yetkazib berish')),
    ]
    BRANCH_CHOICES = (
        (0, 'Stroy baza'),
        (1, 'Giaz mebel'),
        (2, 'Gold Klinker'),
    )
    is_paid = models.BooleanField(default=False)
    part = models.IntegerField(default=0, choices=BRANCH_CHOICES)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    cashback_used = models.DecimalField(max_digits=10, decimal_places=2, default=0, null=True, blank=True)
    cashback_earned = models.DecimalField(max_digits=10, decimal_places=2, default=0, null=True, blank=True)
    status = models.CharField(_("Holat"), max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(_("Yaratilgan sana"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Yangilangan sana"), auto_now=True)
    delivery_date = models.DateField(_("Yetkazib berish sanasi"), null=True, blank=True)
    payment_method = models.CharField(_("To'lov usuli"), max_length=20, choices=PAYMENT_CHOICES, null=True, blank=True)
    delivery_method = models.CharField(_("Yetkazib berish usuli"), max_length=20, choices=DELIVERY_CHOICES, null=True, blank=True)
    delivery_address = models.TextField(_("Yetkazib berish manzili"), null=True, blank=True)
    total_amount = models.DecimalField(_("Umumiy summa"), max_digits=10, decimal_places=2, null=True, blank=True, default=0)
    branch = models.ForeignKey(to='Branch', related_name='Branch', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"Buyurtma {self.id} - {self.user.username}"

    def calculate_total(self):
        return self.items.aggregate(total=Sum(F('price') * F('quantity')))['total'] or 0



    class Meta:
        verbose_name = _("Buyurtma")
        verbose_name_plural = _("Buyurtmalar")


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', verbose_name=_("Buyurtma"))
    product_variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, verbose_name=_("Mahsulot varianti"))
    quantity = models.PositiveIntegerField(_("Miqdori"))
    price = models.DecimalField(_("Narx"), max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} x {self.product_variant} in Buyurtma {self.order.id}"

    class Meta:
        verbose_name = _("Buyurtma elementi")
        verbose_name_plural = _("Buyurtma elementlari")


class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites', verbose_name=_("Foydalanuvchi"))
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name=_("Mahsulot"))

    class Meta:
        unique_together = ('user', 'product')
        verbose_name = _("Sevimli")
        verbose_name_plural = _("Sevimlilar")

    def __str__(self):
        return f"{self.user.username}ning sevimlisi: {self.product.name_uz}"


class Banner(models.Model):
    BRANCH_CHOICES = (
        (0, 'Stroy baza'),
        (1, 'Giaz mebel'),
        (2, 'Gold Klinker'),
    )
    branch = models.IntegerField(default=0, choices=BRANCH_CHOICES)
    image = models.ImageField(_("Rasm"), upload_to='banner_images/', null=True, blank=True)
    is_active = models.BooleanField(_("Faol"), default=True)

    class Meta:
        verbose_name = _("Banner")
        verbose_name_plural = _("Bannerlar")


class UserAgreement(models.Model):
    BRANCH_CHOICES = (
        (0, 'Stroy baza'),
        (1, 'Giaz mebel'),
        (2, 'Gold Klinker'),
    )
    branch = models.IntegerField(default=0, choices=BRANCH_CHOICES)
    title_uz = models.CharField(_("Sarlavha (O'zbek)"), max_length=200)
    title_ru = models.CharField(_("Заголовок (Русский)"), max_length=200)
    title_en = models.CharField(_("Title (English)"), max_length=200)
    content_uz = models.TextField(_("Mazmun (O'zbek)"))
    content_ru = models.TextField(_("Содержание (Русский)"))
    content_en = models.TextField(_("Content (English)"))
    version = models.CharField(_("Versiya"), max_length=10)
    is_active = models.BooleanField(_("Faol"), default=True)
    created_at = models.DateTimeField(_("Yaratilgan sana"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Yangilangan sana"), auto_now=True)

    def __str__(self):
        return f"{self.title_uz} - v{self.version}"

    class Meta:
        verbose_name = _("Foydalanuvchi shartnomasi")
        verbose_name_plural = _("Foydalanuvchi shartnomalari")

class Support(models.Model):
    BRANCH_CHOICES = (
        (0, 'Stroy baza'),
        (1, 'Giaz mebel'),
        (2, 'Gold Klinker'),
    )
    branch = models.IntegerField(default=0, choices=BRANCH_CHOICES)
    title_uz = models.CharField(_("Sarlavha (O'zbek)"), max_length=200)
    title_ru = models.CharField(_("Заголовок (Русский)"), max_length=200)
    title_en = models.CharField(_("Title (English)"), max_length=200)
    phone_number = models.CharField(_("Telefon raqami"), max_length=20)
    is_active = models.BooleanField(_("Faol"), default=True)
    order = models.PositiveIntegerField(_("Tartib"), default=0)

    def __str__(self):
        return self.title_uz

    class Meta:
        verbose_name = _("Qo'llab-quvvatlash")
        verbose_name_plural = _("Qo'llab-quvvatlash xizmatlari")
        ordering = ['order']

class Branch(models.Model):
    BRANCH_CHOICES = (
        (0, 'Stroy baza'),
        (1, 'Giaz mebel'),
        (2, 'Gold Klinker'),
    )
    branch = models.IntegerField(default=0, choices=BRANCH_CHOICES)
    name_uz = models.CharField(_("Nomi (O'zbek)"), max_length=200)
    name_ru = models.CharField(_("Название (Русский)"), max_length=200)
    name_en = models.CharField(_("Name (English)"), max_length=200)
    address_uz = models.TextField(_("Manzil (O'zbek)"))
    address_ru = models.TextField(_("Адрес (Русский)"))
    address_en = models.TextField(_("Address (English)"))
    location = models.ForeignKey('Location', on_delete=models.SET_NULL, null=True, related_name='branches')
    phone = models.CharField(_("Telefon"), max_length=20)
    working_hours_uz = models.CharField(_("Ish vaqti (O'zbek)"), max_length=100)
    working_hours_ru = models.CharField(_("Рабочее время (Русский)"), max_length=100)
    working_hours_en = models.CharField(_("Working Hours (English)"), max_length=100)
    is_active = models.BooleanField(_("Faol"), default=True)
    order = models.PositiveIntegerField(_("Tartib"), default=0)

    def __str__(self):
        return self.name_uz

    class Meta:
        verbose_name = _("Filial")
        verbose_name_plural = _("Filiallar")
        ordering = ['order']

class Location(models.Model):
    latitude = models.DecimalField(_("Kenglik"), max_digits=9, decimal_places=6)
    longitude = models.DecimalField(_("Uzunlik"), max_digits=9, decimal_places=6)
    address_uz = models.TextField(_("Manzil (O'zbek)"))
    address_ru = models.TextField(_("Адрес (Русский)"))
    address_en = models.TextField(_("Address (English)"))
    is_active = models.BooleanField(_("Faol"), default=True)
    is_main = models.BooleanField(_("Asosiy manzil"), default=False)

    def __str__(self):
        return self.address_uz

    class Meta:
        verbose_name = _("Manzil")
        verbose_name_plural = _("Manzillar")


class SocialMedia(models.Model):
    BRANCH_CHOICES = (
        (0, 'Stroy baza'),
        (1, 'Giaz mebel'),
        (2, 'Gold Klinker'),
    )
    branch = models.IntegerField(default=0, choices=BRANCH_CHOICES)
    instagram = models.CharField(_("Instagram havolangiz"), max_length=500)
    telegram = models.CharField(_("Telegram havolangiz"), max_length=500)
    youtube = models.CharField(_("Youtube havolangiz"), max_length=500)



