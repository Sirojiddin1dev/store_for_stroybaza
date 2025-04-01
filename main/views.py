from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .serializers import *
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model, authenticate
from .utils import *
from django.utils import timezone
User = get_user_model()

import logging

logger = logging.getLogger(__name__)
MAX_RESEND_ATTEMPTS = 50
COOLDOWN_PERIOD = timedelta(hours=24)

def get_sms_message(verification_code, action, source):
    """
    Generate SMS message based on action and source
    """
    if source == 'mobile':
        if action == 'register':
            return f"Stroy Baza N1 ilovasidan royxatdan o'tish uchun sizning tasdiqlash kodingiz: {verification_code}"
        elif action == 'login':
            return f"Stroy Baza N1 ilovasiga kirish uchun sizning tasdiqlash kodingiz: {verification_code}"
        else:
            return f"Stroy Baza N1 ilovasidan yangi tasdiqlash kodingiz: {verification_code}"
    else:  # web
        if action == 'register':
            return f"stroybazan1.uz saytidan ro‘yxatdan o‘tish kodi: {verification_code}"
        elif action == 'login':
            return f"stroybazan1.uz saytiga kirish uchun tasdiqlash kodi: {verification_code}"
        else:
            return f"www.stroybazan1.uz saytiga kirish uchun sizning yangi tasdiqlash kodingiz: {verification_code}"

@swagger_auto_schema(
    method='post',
    request_body=VerifyPhoneSerializer,
    responses={
        200: openapi.Response('User verified and tokens provided', schema=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'message': openapi.Schema(type=openapi.TYPE_STRING),
                'refresh': openapi.Schema(type=openapi.TYPE_STRING),
                'access': openapi.Schema(type=openapi.TYPE_STRING),
            }
        )),
        400: openapi.Response('Bad request')
    },
    operation_description="Verify user with phone number and verification code"
)
@api_view(['POST'])
@permission_classes([AllowAny])
def verify_user(request):
    serializer = VerifyPhoneSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    phone_number = serializer.validated_data['phone_number']
    verification_code = serializer.validated_data['verification_code']

    try:
        user = User.objects.get(phone_number=phone_number, verification_code=verification_code)
    except User.DoesNotExist:
        return Response({'error': 'Noto\'g\'ri telefon raqam yoki tasdiqlash kodi'}, status=status.HTTP_400_BAD_REQUEST)

    user.is_phone_verified = True
    user.verification_code = None
    user.save()

    # JWT token yaratish
    refresh = RefreshToken.for_user(user)

    return Response({
        'message': 'Foydalanuvchi tasdiqlandi va tizimga kiritildi',
        'id': user.pk,
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }, status=status.HTTP_200_OK)



@swagger_auto_schema(
    method='post',
    request_body=VerifyPhoneSerializer,
    responses={
        200: openapi.Response('Login successful', schema=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'refresh': openapi.Schema(type=openapi.TYPE_STRING),
                'access': openapi.Schema(type=openapi.TYPE_STRING),
            }
        )),
        400: openapi.Response('Bad request')
    },
    operation_description="Verify phone login with verification code"
)
@api_view(['POST'])
@permission_classes([AllowAny])
def verify_phone_login(request):
    serializer = VerifyPhoneSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    phone_number = serializer.validated_data['phone_number']
    verification_code = serializer.validated_data['verification_code']

    try:
        user = User.objects.get(phone_number=phone_number, verification_code=verification_code)
    except User.DoesNotExist:
        return Response({'error': 'Noto\'g\'ri telefon raqam yoki tasdiqlash kodi'}, status=status.HTTP_400_BAD_REQUEST)

    user.verification_code = None
    user.save()

    refresh = RefreshToken.for_user(user)
    return Response({
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        'id': user.pk
    })


def check_cooldown(user):
    if user.last_verification_attempt and user.verification_code_attempts >= MAX_RESEND_ATTEMPTS:
        time_elapsed = timezone.now() - user.last_verification_attempt
        if time_elapsed < COOLDOWN_PERIOD:
            time_left = COOLDOWN_PERIOD - time_elapsed
            hours_left = int(time_left.total_seconds() / 3600)
            return False, f"Iltimos, {hours_left} soatdan keyin qayta urinib ko'ring."
    return True, ""


@swagger_auto_schema(
    method='post',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'phone_number': openapi.Schema(type=openapi.TYPE_STRING, description='User phone number'),
            'source': openapi.Schema(type=openapi.TYPE_STRING, description='Request source (mobile/web)', default='web')
        },
        required=['phone_number']
    ),
    responses={
        200: openapi.Response('Tasdiqlash kodi yuborildi'),
        400: openapi.Response('Bad request'),
        500: openapi.Response('Internal server error')
    },
    operation_description="Register a new user with phone number"
)
@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    phone_number = request.data.get('phone_number')
    source = request.data.get('source', 'web')  # Default to 'web' if not specified

    if not phone_number:
        return Response({'error': 'Telefon raqam kiritilishi shart'}, status=status.HTTP_400_BAD_REQUEST)

    if source not in ['web', 'mobile']:
        return Response({'error': 'Noto\'g\'ri source qiymati'}, status=status.HTTP_400_BAD_REQUEST)

    user, created = User.objects.get_or_create(phone_number=phone_number)

    if not created and user.is_phone_verified:
        return Response({'error': 'Bu telefon raqam allaqachon ro\'yxatdan o\'tgan'},
                        status=status.HTTP_400_BAD_REQUEST)

    can_send, cooldown_message = check_cooldown(user)
    if not can_send:
        return Response({'error': cooldown_message}, status=status.HTTP_400_BAD_REQUEST)

    if not created:
        user.verification_code_attempts += 1
    else:
        user.username = phone_number
        user.verification_code_attempts = 1

    verification_code = generate_verification_code()
    user.verification_code = verification_code
    user.last_verification_attempt = timezone.now()
    user.save()

    message = get_sms_message(verification_code, 'register', source)
    sms_sent = send_sms(phone_number, message)

    if sms_sent:
        logger.info(f"SMS {phone_number} raqamiga muvaffaqiyatli yuborildi")
        return Response({
            'message': 'Tasdiqlash kodi yuborildi',
            'attempts_left': MAX_RESEND_ATTEMPTS - user.verification_code_attempts
        }, status=status.HTTP_200_OK)
    else:
        logger.error(f"SMS {phone_number} raqamiga yuborib bo'lmadi")
        if created:
            user.delete()
        return Response({'error': 'SMS yuborishda xatolik yuz berdi. Iltimos, keyinroq qayta urinib ko\'ring.'},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@swagger_auto_schema(
    method='post',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'phone_number': openapi.Schema(type=openapi.TYPE_STRING, description='User phone number'),
            'source': openapi.Schema(type=openapi.TYPE_STRING, description='Request source (mobile/web)', default='web')
        },
        required=['phone_number']
    ),
    responses={
        200: openapi.Response('Verification code sent'),
        400: openapi.Response('Bad request')
    },
    operation_description="Start login process with phone number"
)
@api_view(['POST'])
@permission_classes([AllowAny])
def login_with_phone(request):
    phone_number = request.data.get('phone_number')
    source = request.data.get('source', 'web')  # Default to 'web' if not specified

    if not phone_number:
        return Response({'error': 'Telefon raqam kiritilishi shart'}, status=status.HTTP_400_BAD_REQUEST)

    if source not in ['web', 'mobile']:
        return Response({'error': 'Noto\'g\'ri source qiymati'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(phone_number=phone_number)
    except User.DoesNotExist:
        return Response({'error': 'Bu telefon raqam ro\'yxatdan o\'tmagan'}, status=status.HTTP_400_BAD_REQUEST)

    can_send, cooldown_message = check_cooldown(user)
    if not can_send:
        return Response({'error': cooldown_message}, status=status.HTTP_400_BAD_REQUEST)

    verification_code = generate_verification_code()
    user.verification_code = verification_code
    user.verification_code_attempts += 1
    user.last_verification_attempt = timezone.now()
    user.save()

    message = get_sms_message(verification_code, 'login', source)
    sms_sent = send_sms(phone_number, message)

    if sms_sent:
        logger.info(f"SMS {phone_number} raqamiga muvaffaqiyatli yuborildi")
        return Response({
            'message': 'Tasdiqlash kodi yuborildi',
            'attempts_left': MAX_RESEND_ATTEMPTS - user.verification_code_attempts
        }, status=status.HTTP_200_OK)
    else:
        logger.error(f"SMS {phone_number} raqamiga yuborib bo'lmadi")
        return Response({'error': 'SMS yuborishda xatolik yuz berdi. Iltimos, keyinroq qayta urinib ko\'ring.'},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@swagger_auto_schema(
    method='post',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'phone_number': openapi.Schema(type=openapi.TYPE_STRING, description='User phone number'),
            'source': openapi.Schema(type=openapi.TYPE_STRING, description='Request source (mobile/web)', default='web')
        },
        required=['phone_number']
    ),
    responses={
        200: openapi.Response('Verification code resent'),
        400: openapi.Response('Bad request'),
        500: openapi.Response('Internal server error')
    },
    operation_description="Resend verification code to the user's phone number"
)
@api_view(['POST'])
@permission_classes([AllowAny])
def resend_verification_code(request):
    phone_number = request.data.get('phone_number')
    source = request.data.get('source', 'web')  # Default to 'web' if not specified

    if not phone_number:
        return Response({'error': 'Telefon raqam kiritilishi shart'}, status=status.HTTP_400_BAD_REQUEST)

    if source not in ['web', 'mobile']:
        return Response({'error': 'Noto\'g\'ri source qiymati'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(phone_number=phone_number)
    except User.DoesNotExist:
        return Response({'error': 'Bu telefon raqam ro\'yxatdan o\'tmagan'}, status=status.HTTP_400_BAD_REQUEST)

    can_send, cooldown_message = check_cooldown(user)
    if not can_send:
        return Response({'error': cooldown_message}, status=status.HTTP_400_BAD_REQUEST)

    verification_code = generate_verification_code()
    user.verification_code = verification_code
    user.verification_code_attempts += 1
    user.last_verification_attempt = timezone.now()
    user.save()

    message = get_sms_message(verification_code, 'resend', source)
    sms_sent = send_sms(phone_number, message)

    if sms_sent:
        logger.info(f"Yangi tasdiqlash kodi {phone_number} raqamiga muvaffaqiyatli yuborildi")
        return Response({
            'message': 'Yangi tasdiqlash kodi yuborildi',
            'attempts_left': MAX_RESEND_ATTEMPTS - user.verification_code_attempts
        }, status=status.HTTP_200_OK)
    else:
        logger.error(f"Yangi tasdiqlash kodini {phone_number} raqamiga yuborib bo'lmadi")
        return Response({'error': 'SMS yuborishda xatolik yuz berdi. Iltimos, keyinroq qayta urinib ko\'ring.'},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# User pay
@swagger_auto_schema(
    method='get',
    responses={200: UserSerializer}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_detail(request, pk):
    user = get_object_or_404(User, pk=pk)
    serializer = UserSerializer(user)
    return Response(serializer.data)


@swagger_auto_schema(
    method='put',
    request_body=UserUpdateSerializer,
    responses={
        200: UserUpdateSerializer,
        400: 'Bad Request',
        403: 'Forbidden',
        404: 'Not Found'
    },
    operation_description="Update user's first name and last name"
)
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def user_update(request, pk):
    user = get_object_or_404(User, pk=pk)

    # Faqat o'z ma'lumotlarini yangilashga ruxsat berish
    if request.user.pk != user.pk:
        return Response({"error": "Siz faqat o'z ma'lumotlaringizni yangilashingiz mumkin"},
                        status=status.HTTP_403_FORBIDDEN)

    serializer = UserUpdateSerializer(user, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Region pay
@swagger_auto_schema(
    method='get',
    responses={200: RegionSerializer(many=True)}
)
@api_view(['GET'])
@permission_classes([AllowAny])
def region_list(request):
    regions = Region.objects.all()
    serializer = RegionSerializer(regions, many=True)
    return Response(serializer.data)


@swagger_auto_schema(
    method='get',
    responses={200: RegionSerializer}
)
@api_view(['GET'])
@permission_classes([AllowAny])
def region_detail(request, pk):
    region = get_object_or_404(Region, pk=pk)
    serializer = RegionSerializer(region)
    return Response(serializer.data)


# City pay
@swagger_auto_schema(
    method='get',
    responses={200: CitySerializer(many=True)}
)
@api_view(['GET'])
@permission_classes([AllowAny])
def city_list(request):
    cities = City.objects.all()
    serializer = CitySerializer(cities, many=True)
    return Response(serializer.data)


@swagger_auto_schema(
    method='get',
    responses={200: CitySerializer}
)
@api_view(['GET'])
def city_detail(request, pk):
    city = get_object_or_404(City, pk=pk)
    serializer = CitySerializer(city)
    return Response(serializer.data)


# Category pay
@swagger_auto_schema(
    method='get',
    responses={200: CategorySerializer(many=True)}
)
@api_view(['GET'])
@permission_classes([AllowAny])
def category_list(request):
    categories = Category.objects.all()
    serializer = CategorySerializer(categories, many=True)
    return Response(serializer.data)


@swagger_auto_schema(
    method='get',
    responses={200: CategorySerializer}
)
@api_view(['GET'])
@permission_classes([AllowAny])
def category_detail(request, pk):
    category = get_object_or_404(Category, pk=pk)
    serializer = CategorySerializer(category)
    return Response(serializer.data)


@swagger_auto_schema(
    method='get',
    manual_parameters=[
        openapi.Parameter(
            'branch',
            openapi.IN_QUERY,
            description="Branch ID (0: Stroy baza, 1: Giaz mebel, 2: Gold Klinker)",
            type=openapi.TYPE_INTEGER,
            required=False
        )
    ],
    responses={
        200: ProductSerializer(many=True),
        400: 'Bad Request'
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])
def product_list(request):
    branch = request.query_params.get('branch')

    if branch is not None:
        try:
            branch = int(branch)
            products = Product.objects.filter(branch=branch).order_by('-views')  # Ko'rishlar soni bo'yicha kamayish tartibida
        except ValueError:
            return Response(
                {"error": "Branch parametri butun son bo'lishi kerak"},
                status=status.HTTP_400_BAD_REQUEST
            )
    else:
        products = Product.objects.all().order_by('-views')  # Ko'rishlar soni bo'yicha kamayish tartibida

    serializer = ProductSerializer(products, many=True)
    return Response(serializer.data)


@swagger_auto_schema(
    method='get',
    responses={200: ProductSerializer}
)
@api_view(['GET'])
@permission_classes([AllowAny])
def product_detail(request, pk):
    try:
        # Mahsulotni olish
        product = get_object_or_404(Product, pk=pk)

        # Ko'rishlar sonini oshirish
        # F() obyekti orqali race condition'lardan qochish mumkin
        Product.objects.filter(pk=pk).update(views=F('views') + 1)

        # Yangilangan ma'lumotlarni olish
        product.refresh_from_db()

        # Serializatsiya qilish va qaytarish
        serializer = ProductSerializer(product)
        return Response(serializer.data)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




# ProductVariant pay
@swagger_auto_schema(
    method='get',
    responses={200: ProductVariantSerializer(many=True)}
)
@api_view(['GET'])
@permission_classes([AllowAny])
def product_variant_list(request):
    variants = ProductVariant.objects.all()
    serializer = ProductVariantSerializer(variants, many=True)
    return Response(serializer.data)


@swagger_auto_schema(
    method='get',
    responses={200: ProductVariantSerializer}
)
@api_view(['GET'])
@permission_classes([AllowAny])
def product_variant_detail(request, pk):
    variant = get_object_or_404(ProductVariant, pk=pk)
    serializer = ProductVariantSerializer(variant)
    return Response(serializer.data)


# Order pay
@swagger_auto_schema(
    method='get',
    responses={200: OrderSerializer(many=True)}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def order_list(request):
    orders = Order.objects.filter(user=request.user)
    serializer = OrderSerializer(orders, many=True)
    return Response(serializer.data)


@swagger_auto_schema(
    method='post',
    request_body=OrderSerializer,
    responses={201: OrderSerializer}
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def order_create(request):
    serializer = OrderSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(
    method='get',
    responses={200: OrderSerializer}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def order_detail(request, pk):
    order = get_object_or_404(Order, pk=pk)
    if not request.user.is_staff and order.user != request.user:
        return Response(status=status.HTTP_403_FORBIDDEN)
    serializer = OrderSerializer(order)
    return Response(serializer.data)


@swagger_auto_schema(
    method='put',
    request_body=OrderSerializer,
    responses={200: OrderSerializer}
)
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def order_update(request, pk):
    order = get_object_or_404(Order, pk=pk)
    if not request.user.is_staff and order.user != request.user:
        return Response(status=status.HTTP_403_FORBIDDEN)
    serializer = OrderSerializer(order, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# OrderItem pay
@swagger_auto_schema(
    method='get',
    responses={200: OrderItemSerializer(many=True)}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def order_item_list(request):

    items = OrderItem.objects.filter(order__user=request.user)
    serializer = OrderItemSerializer(items, many=True)
    return Response(serializer.data)


@swagger_auto_schema(
    method='post',
    request_body=OrderItemSerializer,
    responses={201: OrderItemSerializer}
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def order_item_create(request):
    serializer = OrderItemSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(
    method='get',
    responses={200: OrderItemSerializer}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def order_item_detail(request, pk):
    item = get_object_or_404(OrderItem, pk=pk)
    if not request.user.is_staff and item.order.user != request.user:
        return Response(status=status.HTTP_403_FORBIDDEN)
    serializer = OrderItemSerializer(item)
    return Response(serializer.data)


@swagger_auto_schema(
    method='put',
    request_body=OrderItemSerializer,
    responses={200: OrderItemSerializer}
)
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def order_item_update(request, pk):
    item = get_object_or_404(OrderItem, pk=pk)
    if not request.user.is_staff and item.order.user != request.user:
        return Response(status=status.HTTP_403_FORBIDDEN)
    serializer = OrderItemSerializer(item, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(
    method='delete',
    responses={204: 'No Content'}
)
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def order_item_delete(request, pk):
    item = get_object_or_404(OrderItem, pk=pk)
    if not request.user.is_staff and item.order.user != request.user:
        return Response(status=status.HTTP_403_FORBIDDEN)
    item.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


# Favorite pay
@swagger_auto_schema(
    method='get',
    responses={200: FavoriteSerializer(many=True)}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def favorite_list(request):
    favorites = Favorite.objects.filter(user=request.user)
    serializer = FavoriteSerializer(favorites, many=True)
    return Response(serializer.data)


@swagger_auto_schema(
    method='post',
    request_body=FavoriteSerializer,
    responses={201: FavoriteSerializer}
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def favorite_create(request):
    serializer = FavoriteSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(
    method='delete',
    responses={204: 'No Content'}
)
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def favorite_delete(request, pk):
    favorite = get_object_or_404(Favorite, pk=pk, user=request.user)
    favorite.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


# Banner pay
@swagger_auto_schema(
    method='get',
    responses={200: BannerSerializer(many=True)}
)
@api_view(['GET'])
@permission_classes([AllowAny])
def banner_list(request):
    banners = Banner.objects.filter(is_active=True)
    serializer = BannerSerializer(banners, many=True)
    return Response(serializer.data)


# UserAgreement pay
@swagger_auto_schema(
    method='get',
    responses={200: UserAgreementSerializer(many=True)}
)
@api_view(['GET'])
@permission_classes([AllowAny])
def user_agreement_list(request):
    agreements = UserAgreement.objects.filter(is_active=True)
    serializer = UserAgreementSerializer(agreements, many=True)
    return Response(serializer.data)


@swagger_auto_schema(
    method='get',
    responses={200: UserAgreementSerializer}
)
@api_view(['GET'])
@permission_classes([AllowAny])
def user_agreement_detail(request, pk):
    agreement = get_object_or_404(UserAgreement, pk=pk)
    serializer = UserAgreementSerializer(agreement)
    return Response(serializer.data)


class SupportListView(generics.ListAPIView):
    queryset = Support.objects.filter(is_active=True)
    serializer_class = SupportSerializer
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_description="Qo'llab-quvvatlash xizmatlarini ro'yxatini olish",
        responses={200: SupportSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class BranchListView(generics.ListAPIView):
    queryset = Branch.objects.filter(is_active=True)
    serializer_class = BranchSerializer
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_description="Filiallar ro'yxatini olish",
        responses={200: BranchSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class LocationListView(generics.ListAPIView):
    queryset = Location.objects.filter(is_active=True)
    serializer_class = LocationSerializer
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_description="Manzillar ro'yxatini olish",
        responses={200: LocationSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class BranchDetailView(generics.RetrieveAPIView):
    queryset = Branch.objects.filter(is_active=True)
    serializer_class = BranchSerializer
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_description="Filial haqida batafsil ma'lumot olish",
        responses={200: BranchSerializer()}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class LocationDetailView(generics.RetrieveAPIView):
    queryset = Location.objects.filter(is_active=True)
    serializer_class = LocationSerializer
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_description="Manzil haqida batafsil ma'lumot olish",
        responses={200: LocationSerializer()}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


@swagger_auto_schema(
    method='get',
    responses={
        200: SocialMediaSerializer(),
        404: 'No social media found'
    },
    operation_description="Get the most recently created social media information"
)
@api_view(['GET'])
@permission_classes([AllowAny])
def get_latest_social_media(request):
    """
    Retrieve the most recently created social media information.
    """
    try:
        latest_social_media = SocialMedia.objects.latest('id')
    except SocialMedia.DoesNotExist:
        return Response({"error": "Ijtimoiy tarmoq ma'lumotlari topilmadi"}, status=status.HTTP_404_NOT_FOUND)

    serializer = SocialMediaSerializer(latest_social_media)
    return Response(serializer.data)
