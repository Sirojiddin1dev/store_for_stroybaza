from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    path('api/resend-verification/', views.resend_verification_code, name='resend-verification'),
    path('api/register/', views.register_user, name='register'),
    path('api/verify/', views.verify_user, name='verify'),
    path('api/login/phone/', views.login_with_phone, name='login-phone'),
    path('api/login/phone/verify/', views.verify_phone_login, name='verify-phone-login'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),

    # User URLs
    path('api/users/<int:pk>/', views.user_detail, name='user-detail'),
    path('api/users/<int:pk>/update/', views.user_update, name='user-update'),

    # Region URLs
    path('api/regions/', views.region_list, name='region-list'),
    path('api/regions/<int:pk>/', views.region_detail, name='region-detail'),

    # City URLs
    path('api/cities/', views.city_list, name='city-list'),
    path('api/cities/<int:pk>/', views.city_detail, name='city-detail'),

    # Category URLs
    path('api/categories/', views.category_list, name='category-list'),
    path('api/categories/<int:pk>/', views.category_detail, name='category-detail'),


    # Product URLs
    path('api/products/', views.product_list, name='product-list'),
    path('api/products/<int:pk>/', views.product_detail, name='product-detail'),


    # ProductVariant URLs
    path('api/product-variants/', views.product_variant_list, name='product-variant-list'),
    path('api/product-variants/<int:pk>/', views.product_variant_detail, name='product-variant-detail'),

    # Order URLs
    path('api/orders/', views.order_list, name='order-list'),
    path('api/orders/create/', views.order_create, name='order-create'),
    path('api/orders/<int:pk>/', views.order_detail, name='order-detail'),
    path('api/orders/<int:pk>/update/', views.order_update, name='order-update'),

    # OrderItem URLs
    path('api/order-items/', views.order_item_list, name='order-item-list'),
    path('api/order-items/create/', views.order_item_create, name='order-item-create'),
    path('api/order-items/<int:pk>/', views.order_item_detail, name='order-item-detail'),
    path('api/order-items/<int:pk>/update/', views.order_item_update, name='order-item-update'),
    path('api/order-items/<int:pk>/delete/', views.order_item_delete, name='order-item-delete'),

    # Favorite URLs
    path('api/favorites/', views.favorite_list, name='favorite-list'),
    path('api/favorites/create/', views.favorite_create, name='favorite-create'),
    path('api/favorites/<int:pk>/delete/', views.favorite_delete, name='favorite-delete'),

    # Banner URLs
    path('api/banners/', views.banner_list, name='banner-list'),

    # UserAgreement URLs
    path('api/user-agreements/', views.user_agreement_list, name='user-agreement-list'),
    path('api/user-agreements/<int:pk>/', views.user_agreement_detail, name='user-agreement-detail'),

    path('supports/', views.SupportListView.as_view(), name='support-list'),
    path('branches/', views.BranchListView.as_view(), name='branch-list'),
    path('locations/', views.LocationListView.as_view(), name='location-list'),
    path('branches/<int:pk>/', views.BranchDetailView.as_view(), name='branch-detail'),
    path('locations/<int:pk>/', views.LocationDetailView.as_view(), name='location-detail'),

    path('api/social-media/latest/', views.get_latest_social_media, name='get-latest-social-media'),


    # path('amo/callback/', amo_callback),

]
