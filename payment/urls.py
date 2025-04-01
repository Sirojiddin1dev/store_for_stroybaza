from django.urls import path
from .views import *
from .pay.click import ClickWebhookAPIView
from .pay.payme import PaymeCallBackAPIView

urlpatterns = [
    path('api/orders/<int:order_id>/payment/', OrderPaymentUpdate.as_view(), name='order-payment-update'),
    path("payme/", PaymeCallBackAPIView.as_view()),
    path("click/", ClickWebhookAPIView.as_view()),
]
