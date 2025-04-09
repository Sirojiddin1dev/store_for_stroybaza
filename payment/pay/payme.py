from payme.types import response
from payme.views import PaymeWebHookAPIView
from payme.models import PaymeTransactions
from main.models import Order
from django.db import transaction


class PaymeCallBackAPIView(PaymeWebHookAPIView):
    """
    Payme webhooklarini qabul qilish va to'lovlarni qayta ishlash uchun API view.
    """

    def check_perform_transaction(self, params):
        account = self.fetch_account(params)
        self.validate_amount(account, params.get('amount'))

        result = response.CheckPerformTransaction(
            allow=True,
            receipt_type=0  # 0 - sotuv, 1 - qaytarish
        )
        order = account
        total_price = sum([item.price * item.quantity for item in order.items.all()])

        for item in order.items.all():
            product = item.product_variant.product

            item_total = item.price * item.quantity
            cashback = order.cashback_used or 0
            discount_share = (item_total / total_price) * cashback if total_price else 0

            response_item = response.Item(
                discount=int(discount_share * 100),  # tiyin format
                title=product.name_uz,
                price=int(item.price * 100),
                count=item.quantity,
                code=product.ikpu,
                units=int(product.units_id),
                vat_percent=12,
                package_code=product.units_id
            )

            result.add_item(response_item)

        return result.as_resp()

    def handle_successfully_payment(self, params, result, *args, **kwargs):
        """
        To'lov muvaffaqiyatli amalga oshirilganda buyurtmani yangilash.
        """
        with transaction.atomic():
            transaction_obj = PaymeTransactions.get_by_transaction_id(transaction_id=params["id"])
            order = Order.objects.select_for_update().get(id=transaction_obj.account_id)

            # Buyurtma holatini "processing" yoki "delivered" ga o'zgartirish
            order.status = 'processing'
            order.is_paid = True
            order.save()

    def handle_cancelled_payment(self, params, result, *args, **kwargs):
        """
        To'lov bekor qilinganda buyurtma holatini o'zgartirish.
        """
        with transaction.atomic():
            transaction_obj = PaymeTransactions.get_by_transaction_id(transaction_id=params["id"])
            order = Order.objects.select_for_update().get(id=transaction_obj.account_id)

            if transaction_obj.state == PaymeTransactions.CANCELED:
                order.status = 'in_payment'
                order.is_paid = False
                order.save()
