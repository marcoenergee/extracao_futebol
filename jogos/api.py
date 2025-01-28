from ninja import Router
from .models import Campeonato,Emissora, Jogo
from typing import List, Optional
from pydantic import BaseModel
from django.db.models import Q
import re



campeonato_router = Router()
jogo_router = Router()
emissora_router = Router()

# Schema para emissoras
class EmissoraSchema(BaseModel):
    id: int
    nome: str
    link: Optional[str]  # Link pode ser opcional

# Schema para jogos (incluindo emissoras)
class JogoSchema(BaseModel):
    id: int
    dia: str
    horario: str
    time_casa: str
    time_casa_logo: Optional[str]
    time_visitante: str
    time_visitante_logo: Optional[str]
    emissoras: List[EmissoraSchema]
    status: Optional[bool] = None

# Schema para serializar os detalhes do campeonato
class CampeonatoSchema(BaseModel):
    id: int
    nome: str
    jogos: List[JogoSchema]
    status: bool = True

# Schema para serializar jogos relacionados a uma emissora
class EmissoraJogoSchema(BaseModel):
    id: int
    dia: str
    horario: str
    time_casa: str
    time_visitante: str
    campeonato_nome: str

@campeonato_router.get("/campeonatos", summary="Listar Campeonatos", tags=["Campeonatos"])
def listar_campeonatos(request):
    campeonatos = Campeonato.objects.all().values("id", "nome", "status")
    return list(campeonatos)

@campeonato_router.get("/{id}/", summary="Detalhar Campeonato", tags=["Campeonatos"])
def detalhar_campeonato(request, id: int):
    try:
        # Carregar o campeonato com jogos e emissoras associadas
        campeonato = Campeonato.objects.prefetch_related("jogos__emissoras").get(id=id)

        # Serializar os dados do campeonato
        jogos = []
        for jogo in campeonato.jogos.all():
            jogos.append({
                "id": jogo.id,
                "dia": jogo.dia,
                "horario": jogo.horario,
                "time_casa": jogo.time_casa,
                "time_casa_logo": jogo.time_casa_logo,
                "time_visitante": jogo.time_visitante,
                "time_visitante_logo": jogo.time_visitante_logo,
                "emissoras": [
                    {
                        "id": emissora.id,
                        "nome": emissora.nome,
                        "link": emissora.link,
                    }
                    for emissora in jogo.emissoras.all()
                ],

                "status": jogo.status
            })

        return {
            "id": campeonato.id,
            "nome": campeonato.nome,
            "link": campeonato.link,
            "jogos": jogos
        }
    except Campeonato.DoesNotExist:
        return {"detail": "Campeonato não encontrado"}, 404


@campeonato_router.get("/{id}/jogos/", summary="Listar Jogos por Campeonato", tags=["Campeonatos"])
def listar_jogos_por_campeonato(request, id: int):
    try:
        jogos = Jogo.objects.filter(campeonato_id=id).prefetch_related("emissoras")
        jogos_serializados = [
            {
                "id": jogo.id,
                "dia": jogo.dia,
                "horario": jogo.horario,
                "time_casa": jogo.time_casa,
                "time_visitante": jogo.time_visitante,
                "emissoras": [
                    {
                        "id": emissora.id,
                        "nome": emissora.nome,
                        "link": emissora.link,
                    }
                    for emissora in jogo.emissoras.all()
                ],
                "status" : jogo.status
            }
            for jogo in jogos
        ]
        return jogos_serializados
    except Campeonato.DoesNotExist:
        return {"detail": "Campeonato não encontrado"}, 404

# Listar emissoras
@emissora_router.get("/emissoras/", response=List[EmissoraSchema], summary="Listar Emissoras", tags=["Emissoras"])
def listar_emissoras(request):
    emissoras = Emissora.objects.all()
    emissoras_serializadas = [
        {"id": emissora.id, "nome": emissora.nome, "link": emissora.link or ""}
        for emissora in emissoras
    ]
    return emissoras_serializadas

# Endpoint para detalhar jogos por emissora
@emissora_router.get("/{id}/", summary="Jogos por Emissora", tags=["Emissoras"])
def detalhar_emissora(request, id: int):
    try:
        # Busca a emissora pelo ID
        emissora = Emissora.objects.prefetch_related("jogos__campeonato").get(id=id)
        
        # Serializa os jogos relacionados
        jogos = [
            {
                "id": jogo.id,
                "dia": jogo.dia,
                "horario": jogo.horario,
                "time_casa": jogo.time_casa,
                "time_visitante": jogo.time_visitante,
                "campeonato_nome": jogo.campeonato.nome,
                "status": jogo.status
            }
            for jogo in emissora.jogos.all()
        ]
        
        # Retorna os dados da emissora com os jogos relacionados
        return {
            "id": emissora.id,
            "nome": emissora.nome,
            "link": emissora.link,
            "jogos": jogos,
        }
    except Emissora.DoesNotExist:
        return {"detail": "Emissora não encontrada"}, 404

@jogo_router.get("/jogos/", response=List[JogoSchema], summary="Listar Jogos", tags=["Jogos"])
def listar_jogos(request):
    jogos = Jogo.objects.prefetch_related("emissoras").all()

    # Serializar os jogos
    jogos_serializados = [
        {
            "id": jogo.id,
            "dia": jogo.dia,
            "horario": jogo.horario,
            "time_casa": jogo.time_casa,
            "time_casa_logo": jogo.time_casa_logo,
            "time_visitante": jogo.time_visitante,
            "time_visitante_logo": jogo.time_visitante_logo,
            "emissoras": [
                {
                    "id": emissora.id,
                    "nome": emissora.nome,
                    "link": emissora.link,
                }
                for emissora in jogo.emissoras.all()
            ],
            "status" : jogo.status,
        }
        for jogo in jogos
    ]

    return jogos_serializados

@jogo_router.get("/{id}/", response=JogoSchema, summary="Detalhar Jogo", tags=["Jogos"])
def detalhar_jogo(request, id: int):
    try:
        jogo = Jogo.objects.prefetch_related("emissoras").get(id=id)

        # Serializar o jogo
        jogo_serializado = {
            "id": jogo.id,
            "dia": jogo.dia,
            "horario": jogo.horario,
            "time_casa": jogo.time_casa,
            "time_casa_logo": jogo.time_casa_logo,
            "time_visitante": jogo.time_visitante,
            "time_visitante_logo": jogo.time_visitante_logo,
            "emissoras": [
                {
                    "id": emissora.id,
                    "nome": emissora.nome,
                    "link": emissora.link,
                }
                for emissora in jogo.emissoras.all()
            ],
            "status" : jogo.status
        }

        return jogo_serializado
    except Jogo.DoesNotExist:
        return {"detail": "Jogo não encontrado"}, 404

@jogo_router.get("/filtrar", summary="Listar Jogos por Data", tags=["Jogos"])
def listar_jogos_por_data(request, dia: str):
    # Extrair apenas a data no formato "dd/mm/yyyy"
    # uma expressão regular para extrair a data
    match = re.search(r'\d{2}/\d{2}/\d{4}', dia)
    if match:
        dia_formatado = match.group(0)  # Isso vai pegar a data no formato "dd/mm/yyyy"
    else:
        return {"error": "Data não encontrada na consulta"}

    # Filtrando os jogos onde a data (dia_formatado) está contida na string 'dia' no banco
    jogos = Jogo.objects.filter(dia__icontains=dia_formatado).prefetch_related("emissoras")
    jogos_serializados = [
        {
            "id": jogo.id,
            "dia": jogo.dia,
            "horario": jogo.horario,
            "time_casa": jogo.time_casa,
            "time_visitante": jogo.time_visitante,
            "emissoras": [
                {
                    "id": emissora.id,
                    "nome": emissora.nome,
                    "link": emissora.link,
                }
                for emissora in jogo.emissoras.all()
            ],
            "status" : jogo.status
        }
        for jogo in jogos
    ]
    return jogos_serializados

@jogo_router.get("/times", summary="Listar Jogos entre Times Específicos", tags=["Jogos"])
def listar_jogos_por_times(request, time_casa: str, time_visitante: str):
    jogos = Jogo.objects.filter(time_casa__icontains=time_casa, time_visitante__icontains=time_visitante).prefetch_related("emissoras")
    jogos_serializados = [
        {
            "id": jogo.id,
            "dia": jogo.dia,
            "horario": jogo.horario,
            "time_casa": jogo.time_casa,
            "time_visitante": jogo.time_visitante,
            "emissoras": [
                {
                    "id": emissora.id,
                    "nome": emissora.nome,
                    "link": emissora.link,
                }
                for emissora in jogo.emissoras.all()
            ],
            "status" : jogo.status
        }
        for jogo in jogos
    ]
    return jogos_serializados

@jogo_router.get("/time", summary="Listar Jogos de um Time Específico", tags=["Jogos"])
def listar_jogos_por_time(request, time: str):
    jogos = Jogo.objects.filter(Q(time_casa__icontains=time) | Q(time_visitante__icontains=time)).prefetch_related("emissoras")
    jogos_serializados = [
        {
            "id": jogo.id,
            "campeonato": jogo.campeonato.nome,
            "dia": jogo.dia,
            "horario": jogo.horario,
            "time_casa": jogo.time_casa,
            "time_visitante": jogo.time_visitante,
            "emissoras": [
                {
                    "id": emissora.id,
                    "nome": emissora.nome,
                    "link": emissora.link,
                }
                for emissora in jogo.emissoras.all()
            ],
            "status" : jogo.status
        }
        for jogo in jogos
    ]
    return jogos_serializados
