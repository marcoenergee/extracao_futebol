from django.contrib import admin
from ninja import NinjaAPI
from django.urls import path
from jogos.api import  campeonato_router
from jogos.api import  jogo_router
from jogos.api import  emissora_router
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

api = NinjaAPI(title="Sistema de Extração de Jogos")

api.add_router("/campeonatos/", campeonato_router)
api.add_router("/jogos/", jogo_router)
api.add_router("/emissoras/", emissora_router)




urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', api.urls),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
]

