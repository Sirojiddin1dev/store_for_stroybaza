from rest_framework import views, status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from payme import Payme
from django.conf import settings

from main.models import Order
from main.serializers import OrderSerializer


class OrderPaymentUpdate(views.APIView):
    """
    API endpoint for updating an order with payment information.
    """
    serializer_class = OrderSerializer

    @swagger_auto_schema(
        operation_description="Update an order with payment information",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['payment_method'],
            properties={
                'payment_method': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Payment method (payme, click, cash)",
                    enum=["payme", "click", "cash"]
                ),
            }
        ),
        responses={
            200: openapi.Response(
                description="Order updated successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'order': openapi.Schema(type=openapi.TYPE_OBJECT),
                        'payment_link': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description="Payment link (only for payme or click)"
                        ),
                    }
                )
            ),
            400: "Bad Request",
            404: "Order not found"
        }
    )
    def put(self, request, order_id):
        """
        Update an existing order with payment information.
        """
        # Buyurtmani topish
        order = get_object_or_404(Order, id=order_id)

        # Faqat to'lov usulini yangilash
        payment_method = request.data.get('payment_method')
        if not payment_method:
            return Response(
                {"error": "payment_method maydoni talab qilinadi"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if payment_method not in ['payme', 'click', 'cash']:
            return Response(
                {"error": "payment_method qiymati payme, click yoki cash bo'lishi kerak"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Buyurtmani yangilash
        order.payment_method = payment_method
        order.save()

        # Serializer orqali ma'lumotlarni qaytarish
        serializer = self.serializer_class(order)

        result = {
            "order": serializer.data
        }

        if payment_method == "payme":
            try:
                # Qaysi kassa ishlatilishini aniqlash
                if order.part in [0, 2]:
                    payme_id = settings.PAYME_ID_1  # Birinchi kassa
                elif order.part == 1:
                    payme_id = settings.PAYME_ID_2  # Ikkinchi kassa
                else:
                    return Response({"error": "Noto‘g‘ri part qiymati."}, status=status.HTTP_400_BAD_REQUEST)

                # To‘lov tizimini boshlash
                payme = Payme(payme_id=payme_id)
                payment_link = payme.initializer.generate_pay_link(
                    id=order.id,
                    amount=int(float(order.total_amount)),  # Tiyin/kopeyka hisobida
                    return_url={settings.FRONTEND_URL}
                )

                result["payment_link"] = payment_link

            except Exception as e:
                return Response(
                    {"error": f"Payme to‘lov havolasini yaratishda xatolik: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        elif payment_method == "click":
            try:
                from click_up import ClickUp
                click_up = ClickUp(
                    service_id=settings.CLICK_SERVICE_ID,
                    merchant_id=settings.CLICK_MERCHANT_ID,
                    secret_key=settings.CLICK_SECRET_KEY
                )
                payment_link = click_up.initializer.generate_pay_link(
                    id=order.id,
                    amount=int(float(order.total_amount)),  # Tiyin/kopeyka hisobida
                    return_url={settings.FRONTEND_URL}
                )
                result["payment_link"] = payment_link
            except Exception as e:
                return Response(
                    {"error": f"Click to'lov havolasini yaratishda xatolik: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        return Response(result)
