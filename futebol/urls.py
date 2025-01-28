from django.contrib import admin
from ninja import NinjaAPI
from django.urls import path
from jogos.api import  campeonato_router
from jogos.api import  jogo_router
from jogos.api import  emissora_router

api = NinjaAPI(title="Sistema de Extração de Jogos")

api.add_router("/campeonatos/", campeonato_router)
api.add_router("/jogos/", jogo_router)
api.add_router("/emissoras/", emissora_router)




urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', api.urls),

]