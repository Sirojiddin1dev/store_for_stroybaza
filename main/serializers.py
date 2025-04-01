from rest_framework import serializers
from .models import *


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'cashback_balance']


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'phone_number', 'first_name', 'last_name']


class PhoneLoginSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=15)


class VerifyPhoneSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=15)
    verification_code = serializers.CharField(max_length=6)


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(max_length=128, write_only=True)


class RegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        fields = '__all__'

class CitySerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = '__all__'

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class ProductVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariant
        fields = '__all__'

class ProductSerializer(serializers.ModelSerializer):
    variants = ProductVariantSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = '__all__'


class OrderItemSerializer(serializers.ModelSerializer):
    product_variant_id = serializers.IntegerField(write_only=True)
    quantity = serializers.IntegerField(min_value=1)
    class Meta:
        model = OrderItem
        fields = ['id', 'product_variant_id', 'quantity', 'price', 'order']
        extra_kwargs = {
            'order': {'write_only': True}  # Faqat yozish uchun, o'qish uchun emas
        }


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, required=False, write_only=True)

    class Meta:
        model = Order
        fields = [
            "id", "user", "cashback_used", "cashback_earned", "status", "created_at",
            "updated_at", "delivery_date", "payment_method", "delivery_method", "delivery_address",
            "total_amount", "branch", "items", "part"
        ]
        read_only_fields = ["id", "status", "created_at", "updated_at", "cashback_earned"]

    def create(self, validated_data):
        # Items ma'lumotlarini ajratib olish
        items_data = validated_data.pop("items", [])

        # Foydalanuvchi ma'lumotlarini olish
        user = self.context.get('request').user if self.context.get('request') else validated_data.get('user')

        # Agar user validated_data'da bo'lsa va None bo'lmasa, uni saqlash
        if 'user' not in validated_data and user:
            validated_data['user'] = user

        # Order yaratish
        order = Order.objects.create(**validated_data)

        # Umumiy summani hisoblash uchun o'zgaruvchi
        total_amount = Decimal('0')

        # OrderItem'larni yaratish
        for item_data in items_data:
            # product_variant_id ni olish
            product_variant_id = item_data.pop('product_variant_id', None)
            if not product_variant_id:
                continue  # Agar product_variant_id bo'lmasa, keyingi item'ga o'tish

            try:
                # ProductVariant obyektini olish
                product_variant = ProductVariant.objects.get(id=product_variant_id)

                # Agar product variant mavjud bo'lmasa, keyingi item'ga o'tish
                if not product_variant.is_available:
                    continue

                # Miqdor va narxni olish
                quantity = int(item_data.get('quantity', 1))

                # Miqdor 0 dan kichik bo'lmasligi kerak
                if quantity <= 0:
                    continue

                # Narxni product variant'dan olish
                price = product_variant.price

                # OrderItem yaratish
                order_item = OrderItem.objects.create(
                    order=order,
                    product_variant=product_variant,
                    quantity=quantity,
                    price=price
                )

                # Umumiy summani yangilash
                item_total = price * quantity
                total_amount += item_total

            except ProductVariant.DoesNotExist:
                # Agar product variant topilmasa, log qilish
                logger.warning(f"ProductVariant with ID {product_variant_id} not found")
                continue
            except Exception as e:
                # Boshqa xatoliklarni log qilish
                logger.error(f"Error creating OrderItem: {str(e)}")
                continue

        # Agar items bo'lsa va total_amount 0 dan katta bo'lsa, buyurtma summasini yangilash
        if total_amount > 0:
            # Cashback hisoblash (1%)
            cashback_earned = total_amount * Decimal('0.01')

            # Order ma'lumotlarini yangilash
            order.total_amount = total_amount
            order.cashback_earned = cashback_earned

            # O'zgartirilgan maydonlarni saqlash
            order.save(update_fields=['total_amount', 'cashback_earned', 'delivery_date'])

        return order

    def update(self, instance, validated_data):
        # items_data ni validated_data dan ajratib olish
        items_data = validated_data.pop('items', None)

        # Cashback ishlatish uchun ma'lumotlarni olish
        cashback_to_use = validated_data.pop('cashback_to_use', Decimal('0'))

        # Status o'zgarganligini tekshirish
        old_status = instance.status
        new_status = validated_data.get('status', old_status)

        # Agar status 'processing' ga o'zgargan bo'lsa, delivery date ni belgilash
        if old_status != 'processing' and new_status == 'processing':
            from django.utils import timezone
            from datetime import timedelta
            validated_data['delivery_date'] = timezone.now().date() + timedelta(days=1)

        # Boshqa maydonlarni yangilash
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # Agar items_data berilgan bo'lsa, OrderItem larni yangilash
        if items_data is not None:
            # Avvalgi OrderItem larni o'chirish
            instance.items.all().delete()
            instance.total_amount = 0
            # Yangi OrderItem lar yaratish
            total_amount = Decimal(0)
            for item_data in items_data:
                product_variant_id = item_data.pop('product_variant_id')
                try:
                    product_variant = ProductVariant.objects.get(id=product_variant_id)
                    quantity = item_data.get('quantity', 1)
                    price = product_variant.price

                    OrderItem.objects.create(
                        order=instance,
                        product_variant=product_variant,
                        quantity=quantity,
                        price=price
                    )

                    total_amount += price * quantity
                except ProductVariant.DoesNotExist:
                    # Agar product variant topilmasa, xatolikni log qilish mumkin
                    logger.warning(f"ProductVariant with ID {product_variant_id} not found")
                    pass

            # Agar items bo'lsa va total_amount 0 dan katta bo'lsa, buyurtma summasini yangilash
            if total_amount > 0:
                instance.total_amount = total_amount
                if new_status == "processing":
                    # Cashback hisoblash (1%)
                    cashback_earned = total_amount * Decimal('0.01')
                    instance.cashback_earned = cashback_earned

                    # **Foydalanuvchining balansiga qo'shish**
                    if instance.user:
                        user = instance.user
                        user.cashback_balance += cashback_earned
                        user.save(update_fields=['cashback_balance'])

        # Cashback ishlatish
        if cashback_to_use > 0 and instance.user:
            user = instance.user

            # Foydalanuvchining cashback balansini tekshirish
            if user.cashback_balance >= cashback_to_use:
                # Avvalgi ishlatilgan cashback'ni qaytarish (agar bo'lsa)
                if instance.cashback_used and instance.cashback_used > 0:
                    user.cashback_balance += instance.cashback_used

                # Yangi cashback'ni ishlatish
                user.cashback_balance -= cashback_to_use
                user.save(update_fields=['cashback_balance'])

                # Order'ga ishlatilgan cashback'ni saqlash
                instance.cashback_used = cashback_to_use

                # Umumiy summadan cashback'ni ayirish
                if instance.total_amount >= cashback_to_use:
                    instance.total_amount -= cashback_to_use
                else:
                    # Agar cashback umumiy summadan katta bo'lsa, faqat umumiy summa miqdorida ishlatish
                    cashback_used = instance.total_amount
                    user.cashback_balance += (cashback_to_use - cashback_used)
                    user.save(update_fields=['cashback_balance'])
                    instance.cashback_used = cashback_used
                    instance.total_amount = Decimal('0')

        # O'zgarishlarni saqlash
        instance.save()

        return instance


class FavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields = '__all__'

class BannerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Banner
        fields = '__all__'

class UserAgreementSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAgreement
        fields = '__all__'


class SupportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Support
        fields = '__all__'


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = '__all__'


class BranchSerializer(serializers.ModelSerializer):
    location = LocationSerializer(read_only=True)

    class Meta:
        model = Branch
        fields = '__all__'


class SocialMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = SocialMedia
        fields = ['id', 'branch', 'instagram', 'telegram', 'youtube']
