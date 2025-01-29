from django.contrib import admin
from .models import Campeonato, Jogo, Emissora
from django.contrib.auth.models import Group
from admin_interface.models import Theme

# Desregistrar o modelo Group
admin.site.unregister(Group)

# Desregistrar o modelo Theme
admin.site.unregister(Theme)


@admin.register(Campeonato)
class CampeonatoAdmin(admin.ModelAdmin):
    list_display = ("nome", )


@admin.register(Emissora)
class EmissoraAdmin(admin.ModelAdmin):
    list_display = ("nome", "link")


@admin.register(Jogo)
class JogoAdmin(admin.ModelAdmin):
    list_display = ("campeonato", "dia", "horario", "time_casa", "time_visitante")
    list_filter = ("campeonato", "dia")
    search_fields = ("time_casa", "time_visitante", "campeonato__nome")
