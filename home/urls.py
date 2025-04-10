"""
URL configuration for home project.

The `urlpatterns` list routes URLs to pay. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function pay
    1. Add an import:  from my_app import pay
    2. Add a URL to urlpatterns:  path('', pay.home, name='home')
Class-based pay
    1. Add an import:  from other_app.pay import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
import debug_toolbar
from payment.pay.click import ClickWebhookAPIView
from payment.pay.payme import PaymeCallBackAPIView

schema_view = get_schema_view(
   openapi.Info(
      title="Test API",
      default_version='v1',
      description="Test description",
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="contact@snippets.local"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path("api/v1/click/updates/", ClickWebhookAPIView.as_view()),
    path("api/v1/payme/updates/", PaymeCallBackAPIView.as_view()),
    path('admin/', admin.site.urls),
    path('api/', include('main.urls')),
    path('pay/', include('payment.urls')),
    path('swagger<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]


urlpatterns = [
    path('__debug__/', include(debug_toolbar.urls)),
] + urlpatterns
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
