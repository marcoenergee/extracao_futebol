from django.db import models

class Campeonato(models.Model):
    nome = models.CharField(max_length=255)
    status = models.BooleanField(max_length=50, null=True, blank=True, default=True)

    def __str__(self):
        return self.nome


class Emissora(models.Model):
    nome = models.CharField(max_length=255)
    link = models.URLField(max_length=500, blank=True, null=True)

    def __str__(self):
        return self.nome


class Jogo(models.Model):
    campeonato = models.ForeignKey(Campeonato, on_delete=models.CASCADE, related_name="jogos")
    dia = models.CharField(max_length=255)
    horario = models.CharField(max_length=50)
    time_casa = models.CharField(max_length=255)
    time_casa_logo = models.URLField(max_length=500, blank=True, null=True)
    time_visitante = models.CharField(max_length=255)
    time_visitante_logo = models.URLField(max_length=500, blank=True, null=True)
    emissoras = models.ManyToManyField(Emissora, related_name="jogos")
    status = models.BooleanField(max_length=50, null=True, blank=True, default=True)

    def __str__(self):
        return f"{self.time_casa} vs {self.time_visitante} - {self.campeonato.nome}"
