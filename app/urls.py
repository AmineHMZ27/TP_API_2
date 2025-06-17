"""
URL configuration for Project_API project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.shortcuts import redirect
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework_simplejwt.authentication import JWTAuthentication

schema_view = get_schema_view(
    openapi.Info(
        title="Data Lake API",
        default_version='v1',
        description='''Cette API permet d'interagir avec un data lake local contenant des données transactionnelles.
      
      ⚙️ Fonctionnalités principales :
      - Authentification via JWT
      - Droits d’accès personnalisés par fichier
      - Recherche filtrée, pagination, et projection
      - Métriques analytiques
      - Audit complet des accès
      - Repoussage de transactions vers Kafka
      - Déclenchement d’un entraînement machine learning
      - Documentation Swagger interactive''',
        terms_of_service="https://github.com/ChleoH",
        contact=openapi.Contact(email="chleohinn@gmail.com"),
        license=openapi.License(name="For academic use only"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)


swagger_settings = {
    'SECURITY_DEFINITIONS': {
        'Bearer': {
            'type': 'apiKey',
            'in': 'header',
            'name': 'Authorization',
            'description': "Enter `Bearer <your JWT token>`",
        }
    },
}

urlpatterns = [
    path('', lambda request: redirect('schema-swagger-ui')),
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('openapi/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),  # 🔐 Get token
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),  # 🔁 Refresh token
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

