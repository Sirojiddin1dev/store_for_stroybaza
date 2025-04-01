import random
import string
import requests
import logging
from django.conf import settings

import home.settings

logger = logging.getLogger(__name__)

def get_eskiz_token():
    url = "https://notify.eskiz.uz/api/auth/login"
    payload = {
        "email": settings.ESKIZ_EMAIL,
        "password": settings.ESKIZ_PASSWORD
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        result = response.json()
        token = result.get('data', {}).get('token')
        if not token:
            logger.error("Eskiz API dan token olinmadi")
            return None
        logger.info("Eskiz token muvaffaqiyatli olindi")
        return token
    except requests.RequestException as e:
        logger.error(f"Eskiz tokenini olishda xatolik: {str(e)}")
        return None


def send_sms(phone_number, message):
    token = get_eskiz_token()
    if not token:
        logger.error("Eskiz token olib bo'lmadi")
        return False

    url = "https://notify.eskiz.uz/api/message/sms/send"
    payload = {
        "mobile_phone": phone_number,
        "message": message,
        "from": "4546",
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        result = response.json()
        logger.info(f"SMS yuborish natijasi: {result}")
        return result.get('status') == 'waiting'
    except requests.RequestException as e:
        logger.error(f"SMS yuborishda xatolik: {str(e)}")
        if e.response:
            logger.error(f"Eskiz javobi: {e.response.text}")  # API xatolik tafsilotlarini chiqarish
        logger.error(f"So'rov ma'lumotlari: {payload}")
        return False


def generate_verification_code():
    return ''.join([str(random.randint(0, 9)) for _ in range(6)])



