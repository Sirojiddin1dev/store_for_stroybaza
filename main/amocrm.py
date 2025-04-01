# import requests
# import logging
# from django.conf import settings
# from django.shortcuts import redirect
# from django.http import JsonResponse
# from django.utils.timezone import now
# from django.apps import apps
# from datetime import timedelta
#
# logger = logging.getLogger(__name__)
#
# AMOCRM_DOMAIN = 'stroybazaandijon.amocrm.ru'
# AMOCRM_CLIENT_ID = settings.AMOCRM_CLIENT_ID
# AMOCRM_CLIENT_SECRET = settings.AMOCRM_CLIENT_SECRET
# AMOCRM_REDIRECT_URI = settings.AMOCRM_REDIRECT_URI
#
#
# def get_access_token():
#     """Bazadan access tokenni olib keladi, muddati tugagan bo'lsa yangilaydi."""
#     AmoCRMToken = apps.get_model('main', 'AmoCRMToken')  # Model nomini string sifatida chaqiramiz
#
#     token = AmoCRMToken.objects.first()
#     if not token or not token.access_token:
#         return None
#
#     if token.expires_at and now() >= token.expires_at:
#         logger.info("Access token muddati tugagan, yangilanmoqda...")
#         refresh_access_token(token)
#
#     return token.access_token
#
#
# def refresh_access_token(token):
#     """OAuth 2.0 tokenni yangilash"""
#     url = f"https://{AMOCRM_DOMAIN}/oauth2/access_token"
#     data = {
#         "client_id": AMOCRM_CLIENT_ID,
#         "client_secret": AMOCRM_CLIENT_SECRET,
#         "grant_type": "refresh_token",
#         "refresh_token": token.refresh_token,
#         "redirect_uri": AMOCRM_REDIRECT_URI
#     }
#     try:
#         response = requests.post(url, json=data)
#         response.raise_for_status()
#         new_tokens = response.json()
#         token.access_token = new_tokens['access_token']
#         token.refresh_token = new_tokens['refresh_token']
#         token.expires_at = now() + timedelta(seconds=new_tokens['expires_in'])
#         token.save()
#         logger.info("AmoCRM token muvaffaqiyatli yangilandi.")
#     except requests.RequestException as e:
#         logger.error(f"Tokenni yangilashda xatolik: {str(e)}")
#
#
# def amo_callback(request):
#     AmoCRMToken = apps.get_model('main', 'AmoCRMToken')  # Model nomini string sifatida chaqiramiz
#
#     """OAuth dan so‘ng kodni qabul qilish"""
#     code = request.GET.get('code')
#     if not code:
#         return JsonResponse({"error": "Kod berilmagan"}, status=400)
#
#     url = f"https://{AMOCRM_DOMAIN}/oauth2/access_token"
#     data = {
#         "client_id": AMOCRM_CLIENT_ID,
#         "client_secret": AMOCRM_CLIENT_SECRET,
#         "grant_type": "authorization_code",
#         "code": code,
#         "redirect_uri": AMOCRM_REDIRECT_URI
#     }
#     try:
#         response = requests.post(url, json=data)
#         response.raise_for_status()
#         tokens = response.json()
#         AmoCRMToken.objects.update_or_create(
#             id=1,
#             defaults={
#                 "access_token": tokens['access_token'],
#                 "refresh_token": tokens['refresh_token'],
#                 "expires_at": now() + timedelta(seconds=tokens['expires_in'])
#             }
#         )
#         logger.info("OAuth muvaffaqiyatli yakunlandi.")
#         return redirect("/admin")
#     except requests.RequestException as e:
#         logger.error(f"OAuth xatolik: {str(e)}")
#         return JsonResponse({"error": "OAuth xatolik"}, status=400)
#
#
# def get_pipeline_id(order_part):
#     """Orderning part maydoniga qarab to‘g‘ri pipeline ID ni qaytaradi."""
#     pipeline_map = {
#         'stroybaza': 9307862,
#         'goldklinker': 9309122,
#         'giaz mebel': 9309118
#     }
#     return pipeline_map.get(order_part.lower(), 9307862)  # Default qiymat: stroybaza
#
#
# def send_order_to_amocrm(order):
#     """Buyurtmani AmoCRM'ga yuborish yoki yangilash"""
#     if order.status == 'pending':
#         return False, "Pending buyurtmalar yuborilmaydi"
#
#     access_token = get_access_token()
#     if not access_token:
#         return False, "OAuth token mavjud emas"
#
#     headers = {"Authorization": f"Bearer {access_token}"}
#
#     lead_data = {
#         "name": f"Buyurtma #{order.id}",
#         "price": int(float(order.total_amount)),
#         "pipeline_id": get_pipeline_id(order.part),
#         "status_id": get_amocrm_status_id(order.status),
#         "custom_fields_values": [
#             {"field_code": "PHONE", "values": [{"value": order.user.phone_number if order.user else ""}]},
#             {"field_code": "ADDRESS", "values": [{"value": order.delivery_address or ""}]},
#             {"field_code": "ORDER_DETAILS", "values": [{"value": get_order_details(order)}]},
#             {"field_code": "PART", "values": [{"value": order.part}]}
#         ]
#     }
#
#     if order.amocrm_lead_id:  # **Eskisini yangilash**
#         url = f"https://{AMOCRM_DOMAIN}/api/v4/leads/{order.amocrm_lead_id}"
#         try:
#             response = requests.patch(url, json=lead_data, headers=headers)
#             response.raise_for_status()
#             return True, "AmoCRM lead yangilandi"
#         except requests.RequestException as e:
#             return False, f"AmoCRM'ni yangilashda xatolik: {str(e)}"
#
#     else:  # **Yangi lead yaratish**
#         url = f"https://{AMOCRM_DOMAIN}/api/v4/leads"
#         try:
#             response = requests.post(url, json=[lead_data], headers=headers)
#             response.raise_for_status()
#             result = response.json()
#             if result.get('_embedded', {}).get('leads'):
#                 order.amocrm_lead_id = result['_embedded']['leads'][0]['id']
#                 order.save(update_fields=['amocrm_lead_id'])
#                 return True, "Yangi AmoCRM lead yaratildi"
#             else:
#                 return False, "AmoCRM'dan lead ID olinmadi"
#         except requests.RequestException as e:
#             return False, f"AmoCRM'ga yuborishda xatolik: {str(e)}"
#
#
# def get_amocrm_status_id(order_status):
#     status_map = {
#         'pending': 58319062,
#         'processing': 58319066,
#         'shipped': 58319070,
#         'delivered': 58319074,
#         'cancelled': 58319078
#     }
#     return status_map.get(order_status, 58319062)
#
#
# def get_order_details(order):
#     details = [
#         f"Buyurtma #{order.id}",
#         f"Umumiy summa: {order.total_amount} so'm",
#         f"To'lov usuli: {order.get_payment_method_display()}",
#         f"Yetkazib berish usuli: {order.get_delivery_method_display()}",
#         "\nMahsulotlar:"
#     ]
#     for item in order.items.all():
#         product = item.product_variant.product
#         details.append(
#             f"- {product.name_uz} ({item.product_variant.color_uz}, {item.product_variant.size_uz})"
#             f": {item.quantity} x {item.price} = {item.quantity * item.price} so'm"
#         )
#     return "\n".join(details)
