import logging
import re
from celery import shared_task
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from .models import Campeonato, Jogo, Emissora
from celery.exceptions import MaxRetriesExceededError
from django.db import transaction

# Configuração de logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Configura o handler para escrever logs em um arquivo
file_handler = logging.FileHandler("scrape_campeonato.log")
file_handler.setLevel(logging.INFO)

# Formato dos logs
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

# Adiciona o handler ao logger
logger.addHandler(file_handler)

def salvar_resultados_no_banco(resultados):
    """Salva os resultados acumulados no banco de dados usando transações."""
    logger.info("Iniciando o salvamento dos resultados no banco de dados.")
    
    try:
        with transaction.atomic():  # Inicia uma transação
            for campeonato_nome, jogos in resultados.items():
                # Verifica ou cria o campeonato
                campeonato_obj, created = Campeonato.objects.get_or_create(
                    nome=campeonato_nome
                )
                if created:
                    logger.info(f"Campeonato criado: {campeonato_nome}")

                for jogo in jogos:
                    # Verifica se o jogo já existe
                    jogo_existente = Jogo.objects.filter(
                        campeonato=campeonato_obj,
                        dia=jogo["dia"],
                        horario=jogo["horario"],
                        time_casa=jogo["time_casa"],
                        time_visitante=jogo["time_visitante"],
                    ).exists()

                    if not jogo_existente:
                        # Cria o jogo
                        novo_jogo = Jogo.objects.create(
                            campeonato=campeonato_obj,
                            dia=jogo["dia"],
                            horario=jogo["horario"],
                            time_casa=jogo["time_casa"],
                            time_visitante=jogo["time_visitante"],
                            time_casa_logo=jogo["time_casa_logo"],
                            time_visitante_logo=jogo["time_visitante_logo"],
                        )
                        logger.info(f"Jogo criado: {jogo['time_casa']} vs {jogo['time_visitante']} - {jogo['dia']} {jogo['horario']}")

                        # Adiciona as emissoras associadas ao jogo
                        for emissora in jogo["emissoras"]:
                            emissora_obj, emissora_created = Emissora.objects.get_or_create(
                                nome=emissora["nome"], link=emissora["link"]
                            )
                            novo_jogo.emissoras.add(emissora_obj)
                            if emissora_created:
                                logger.info(f"Nova emissora criada: {emissora['nome']}")
        logger.info("Resultados salvos com sucesso.")
    
    except Exception as e:
        logger.error(f"Erro ao salvar resultados no banco de dados: {e}")
        raise

@shared_task(bind=True, max_retries=10, default_retry_delay=60)
def scrape_campeonato(self):
    logger.info("Iniciando o scraping dos campeonatos.")
    try:
        # Dicionário para acumular resultados
        resultados_acumulados = {}

        with sync_playwright() as p:
            # Inicializa o navegador
            browser = p.chromium.launch(headless=True)  # headless=True para rodar em segundo plano
            context = browser.new_context()
            page = context.new_page()

            # Acessa a página principal
            try:
                page.goto("https://www.futebolaovivobrasil.com/campeonato")
                page.wait_for_selector("ul.listadoEquipos")
                logger.info("Página principal carregada com sucesso.")
            except Exception as e:
                logger.error(f"Erro ao carregar a página principal: {e}")
                browser.close()
                return "Erro ao carregar a página principal."

            # Pega todos os campeonatos na lista
            campeonatos = page.query_selector_all("ul.listadoEquipos > li > a")
            logger.info(f"Encontrados {len(campeonatos)} campeonatos na lista.")

            # Itera por cada campeonato
            for i, campeonato in enumerate(campeonatos):
                try:
                    campeonatos = page.query_selector_all("ul.listadoEquipos > li > a")
                    campeonato_atual = campeonatos[i]
                    #campeonato_nome = campeonato_atual.text_content().strip()
                    campeonato_nome = re.sub(r"\s*\(\d+\)$", "", campeonato_atual.text_content().strip())
                    logger.info(f"Entrando no campeonato: {campeonato_nome}")

                    # Clica no campeonato
                    campeonato_atual.click()
                    page.wait_for_selector("table.tablaPrincipal", timeout=60000)

                    # Extrai o HTML da página carregada
                    soup = BeautifulSoup(page.content(), "html.parser")

                    # Encontra todas as tabelas de jogos
                    tabelas = soup.find_all("table", class_="tablaPrincipal")
                    resultados_acumulados[campeonato_nome] = []

                    for tabela in tabelas:
                        rows = tabela.find_all("tr")
                        dia = None
                        for row in rows:
                            columns = row.find_all("td")
                            dados = [col.text.strip() for col in columns]
                            if len(dados) == 1:  # Linha com o dia
                                dia = dados[0]
                            elif len(dados) >= 5:  # Linha com informações do jogo
                                time_casa_logo = (
                                    columns[2].find("img")["src"] if columns[2].find("img") else None
                                )
                                time_visitante_logo = (
                                    columns[3].find("img")["src"] if columns[3].find("img") else None
                                )
                                emissoras = [
                                    {"nome": a.text.strip(), "link": a["href"]}
                                    for a in columns[4].find_all("a", href=True)
                                ]
                                jogo = {
                                    "dia": dia,
                                    "horario": dados[0],
                                    "campeonato": dados[1],
                                    "time_casa": dados[2],
                                    "time_casa_logo": time_casa_logo,
                                    "time_visitante": dados[3],
                                    "time_visitante_logo": time_visitante_logo,
                                    "emissoras": emissoras,
                                }
                                resultados_acumulados[campeonato_nome].append(jogo)

                    logger.info(f"Jogos do campeonato {campeonato_nome} extraídos com sucesso.")

                    # Volta para a página inicial
                    page.goto("https://www.futebolaovivobrasil.com/campeonato")
                    page.wait_for_selector("ul.listadoEquipos")

                except Exception as e:
                    logger.error(f"Erro ao processar o campeonato {campeonato_nome}: {e}")
                    page.goto("https://www.futebolaovivobrasil.com/campeonato")
                    page.wait_for_selector("ul.listadoEquipos")
                    continue

            # Fecha o navegador
            browser.close()
            logger.info("Navegador fechado.")

        # Salvar os resultados acumulados no banco de dados
        salvar_resultados_no_banco(resultados_acumulados)
        logger.info("Resultados salvos no banco de dados.")

    except Exception as exc:
        logger.error(f"Erro na task: {exc}")
        try:
            self.retry(exc=exc)  # Retenta a task em caso de erro
        except MaxRetriesExceededError:
            logger.error("Número máximo de tentativas excedido.")
            raise
