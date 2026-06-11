"""
URL configuration for services_aiori_v2 project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
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
from rest_framework_simplejwt import views as jwt_views
from django.conf.urls.static import static
from django.conf.urls import handler404, handler500

from services_aiori_v2 import settings

urlpatterns = [
    path('admin/', admin.site.urls),

    # For JWT Token url in jwt plugin
    path('api/token/', jwt_views.TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', jwt_views.TokenRefreshView.as_view(), name='token_refresh'),


    path('', include('backend.services_app.urls', namespace='services_app')),
    path('api-app/', include('backend.api_app.urls', namespace='api_app')),
    path('api/user/', include('backend.users.urls', namespace='users')),
    # path('api/users/', include('backend.users.urls')),
    path('api/common/', include('backend.common.urls', namespace='common')),
    path('api/subscription/', include('backend.subscription.urls', namespace='common')),
    path('api/anchor/', include('backend.anchor.urls', namespace='anchor')),
]
# + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
handler404 = 'backend.services_app.views.custom_404_view'
handler500 = 'backend.services_app.views.custom_500_view'