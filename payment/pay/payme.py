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
        """
        To'lovni amalga oshirish mumkinligini tekshirish.
        """
        account = self.fetch_account(params)
        self.validate_amount(account, params.get('amount'))

        result = response.CheckPerformTransaction(allow=True)

        # Statik ma'lumotlar o'rniga buyurtma haqida dinamik ma'lumotlarni qo'shish mumkin
        order = account

        item = response.Item(
            discount=0,
            title=f"Buyurtma #{order.id}",
            price=int(order.total_amount * 100),
            count=1,
            code=str(order.id),
            units=1,
            vat_percent=15,
            package_code="123456"
        )

        result.add_item(item)
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
