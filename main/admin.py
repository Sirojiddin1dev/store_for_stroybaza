from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from django.forms import ModelForm
from django.db import models as django_models
from django.contrib.admin import widgets as admin_widgets
from .models import *


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('get_full_name', 'username', 'phone_number', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_active', 'groups')
    search_fields = ('username', 'first_name', 'last_name', 'phone_number')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email', 'phone_number')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
        (_('Additional info'), {'fields': ('city', 'cashback_balance', 'is_phone_verified')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'phone_number', 'password1', 'password2'),
        }),
    )

    def get_full_name(self, obj):
        if obj.first_name and obj.last_name:
            return f"{obj.first_name} {obj.last_name}"
        return obj.username
    get_full_name.short_description = _('Full Name')


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ('name_uz', 'name_ru', 'name_en')
    search_fields = ('name_uz', 'name_ru', 'name_en')


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ('name_uz', 'name_ru', 'name_en', 'region')
    list_filter = ('region',)
    search_fields = ('name_uz', 'name_ru', 'name_en')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name_uz', 'name_ru', 'name_en', 'branch')
    list_filter = ('branch',)
    search_fields = ('name_uz', 'name_ru', 'name_en')


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1
    readonly_fields = ('monthly_payment_3', 'monthly_payment_6', 'monthly_payment_12', 'monthly_payment_24')

    fields = (
        'size_uz', 'size_ru', 'size_en',
        'color_uz', 'color_ru', 'color_en',
        'price', 'is_available', 'image',
        'monthly_payment_3', 'monthly_payment_6',
        'monthly_payment_12', 'monthly_payment_24'
    )

    verbose_name = _("Mahsulot varianti")
    verbose_name_plural = _("Mahsulot variantlari")

    formfield_overrides = {
        django_models.ImageField: {'widget': admin_widgets.AdminFileWidget},
    }

    def get_fieldsets(self, request, obj=None):
        fieldsets = (
            (_('O\'lcham'), {
                'fields': ('size_uz', 'size_ru', 'size_en'),
            }),
            (_('Rang'), {
                'fields': ('color_uz', 'color_ru', 'color_en'),
            }),
            (_('Narx va Mavjudlik'), {
                'fields': ('price', 'is_available'),
            }),
            (_('Rasm'), {
                'fields': ('image',),
            }),
            (_('Oylik to\'lov'), {
                'fields': (
                    'monthly_payment_3', 'monthly_payment_6',
                    'monthly_payment_12', 'monthly_payment_24'
                ),
            }),
        )
        return fieldsets


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name_uz', 'name_ru', 'name_en', 'category', 'is_available', 'branch')
    list_filter = ('category', 'is_available', 'branch')
    search_fields = ('name_uz', 'name_ru', 'name_en',
                     'description_uz', 'description_ru', 'description_en')
    inlines = [ProductVariantInline]
    fieldsets = (
        (None, {
            'fields': ('category', 'is_available', 'branch', "views")
        }),
        (_('Names'), {
            'fields': ('name_uz', 'name_ru', 'name_en')
        }),
        (_('Descriptions'), {
            'fields': ('description_uz', 'description_ru', 'description_en')
        }),
        (_('Image'), {
            'fields': ('image',)
        }),
    )

    def save_formset(self, request, form, formset, change):
        """
        Mahsulot variantlarini saqlashdan oldin tekshirish
        """
        variants = formset.save(commit=False)

        # Agar bu yangi mahsulot bo'lsa va variantlar bo'sh bo'lsa
        if not change and len(variants) == 0:
            raise ValidationError(_("Kamida bitta mahsulot varianti kiritilishi shart."))

        # Kamida bitta variant narxi kiritilganligini tekshirish
        has_price = False
        for variant in variants:
            if variant.price and variant.price > 0:
                has_price = True
                break

        # Agar narx kiritilmagan bo'lsa
        if not has_price and not change:
            raise ValidationError(_("Kamida bitta mahsulot varianti uchun narx kiritilishi shart."))

        # Variantlarni saqlash
        for variant in variants:
            variant.save()

        # O'chirilgan variantlarni o'chirish
        formset.save_m2m()

    def save_model(self, request, obj, form, change):
        """
        Mahsulotni saqlash
        """
        super().save_model(request, obj, form, change)

        # Agar bu yangi mahsulot bo'lsa, variantlar sonini tekshirish
        if not change:
            variants_count = obj.variants.count()
            if variants_count == 0:
                # Bu xato ko'rsatilmaydi, chunki variantlar keyinroq saqlanadi
                # Lekin save_formset metodida tekshiriladi
                pass


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1
    readonly_fields = ('product_variant', 'quantity', 'price')
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'status', 'total_amount', 'created_at', 'is_paid', 'part')
    list_filter = ('status', 'payment_method', 'delivery_method', 'is_paid')
    search_fields = ('user__username', 'user__email', 'delivery_address')
    inlines = [OrderItemInline]
    readonly_fields = ('user', 'total_amount', 'cashback_used', 'cashback_earned',
                       'created_at', 'updated_at', 'delivery_date', 'payment_method',
                       'delivery_method', 'delivery_address', 'branch', 'part')

    fieldsets = (
        (None, {'fields': ('user', 'status', 'total_amount', 'branch', 'part', "is_paid")}),
        (_('Cashback'), {'fields': ('cashback_used', 'cashback_earned')}),
        (_('Delivery'), {'fields': ('delivery_method', 'delivery_date', 'delivery_address')}),
        (_('Payment'), {'fields': ('payment_method',)}),
        (_('Dates'), {'fields': ('created_at', 'updated_at')}),
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False



@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'product')
    list_filter = ('user',)
    search_fields = ('user__username', 'product__name_uz', 'product__name_ru', 'product__name_en')


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ('is_active', 'branch')
    list_filter = ('is_active', 'branch')
    radio_fields = {"branch": admin.HORIZONTAL}
    fieldsets = (
        (None, {'fields': ('is_active', 'branch')}),
        (_('Image'), {'fields': ('image',)}),
    )


@admin.register(UserAgreement)
class UserAgreementAdmin(admin.ModelAdmin):
    list_display = ('title_uz', 'title_ru', 'title_en', 'version', 'is_active', 'created_at', 'updated_at', 'branch')
    list_filter = ('is_active', 'version', 'branch')
    search_fields = ('title_uz', 'title_ru', 'title_en', 'content_uz', 'content_ru', 'content_en')
    fieldsets = (
        (None, {'fields': ('version', 'is_active', 'branch')}),
        (_('Titles'), {'fields': ('title_uz', 'title_ru', 'title_en')}),
        (_('Contents'), {'fields': ('content_uz', 'content_ru', 'content_en')}),
    )


@admin.register(Support)
class SupportAdmin(admin.ModelAdmin):
    list_display = ('title_uz', 'phone_number', 'is_active', 'order', 'branch')
    list_filter = ('is_active', 'branch')
    search_fields = ('title_uz', 'title_ru', 'title_en', 'phone_number')
    fieldsets = (
        (None, {'fields': ('is_active', 'order', 'branch')}),
        (_('Contact Info'), {'fields': ('phone_number',)}),
        (_('Titles'), {'fields': ('title_uz', 'title_ru', 'title_en')}),
    )


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ('name_uz', 'address_uz', 'phone', 'is_active', 'order', 'branch')
    list_filter = ('is_active', 'branch')
    search_fields = ('name_uz', 'name_ru', 'name_en', 'address_uz', 'address_ru', 'address_en')
    fieldsets = (
        (None, {'fields': ('is_active', 'order', 'location', 'branch')}),
        (_('Names'), {'fields': ('name_uz', 'name_ru', 'name_en')}),
        (_('Addresses'), {'fields': ('address_uz', 'address_ru', 'address_en')}),
        (_('Contact Info'), {'fields': ('phone', 'working_hours_uz', 'working_hours_ru', 'working_hours_en')}),
    )


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('address_uz', 'latitude', 'longitude', 'is_active', 'is_main')
    list_filter = ('is_active', 'is_main')
    search_fields = ('address_uz', 'address_ru', 'address_en')
    fieldsets = (
        (None, {'fields': ('latitude', 'longitude', 'is_active', 'is_main')}),
        (_('Addresses'), {'fields': ('address_uz', 'address_ru', 'address_en')}),
    )


@admin.register(SocialMedia)
class SocialMediaAdmin(admin.ModelAdmin):
    list_display = ('instagram', 'telegram', 'youtube', 'branch')
    list_filter = ('branch',)
    search_fields = ('instagram', 'telegram', 'youtube')
    fieldsets = (
        (_('Social Media Links'), {
            'fields': ('instagram', 'telegram', 'youtube', 'branch')
        }),
    )
# admin.site.register(AmoCRMToken)