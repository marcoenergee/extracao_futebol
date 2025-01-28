from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup


def scrape_website():
    with sync_playwright() as p:
        # Inicializa o navegador
        browser = p.chromium.launch(headless=False)  # headless=True se quiser rodar em segundo plano
        context = browser.new_context()
        page = context.new_page()

        # Acessa a página principal
        page.goto("https://www.futebolaovivobrasil.com/campeonato")

        # Aguarda até que a lista de campeonatos seja carregada
        page.wait_for_selector("ul.listadoEquipos")

        # Pega todos os campeonatos na lista
        campeonatos = page.query_selector_all("ul.listadoEquipos > li > a")
        resultados = {}

        # Itera por cada campeonato
        for i, campeonato in enumerate(campeonatos):
            try:
                # Reobtém o elemento para evitar problemas de contexto
                campeonatos = page.query_selector_all("ul.listadoEquipos > li > a")
                campeonato_atual = campeonatos[i]  # Reacessa o elemento atual
                campeonato_nome = campeonato_atual.text_content().strip()
                print(f"Entrando no campeonato: {campeonato_nome}")

                # Clica no campeonato
                campeonato_atual.click()

                # Aguarda o carregamento da nova página
                page.wait_for_selector("table.tablaPrincipal", timeout=60000)

                # Extrai o HTML da página carregada
                page_content = page.content()

                # Usa BeautifulSoup para processar o HTML
                soup = BeautifulSoup(page_content, "html.parser")

                # Encontra todas as tabelas de jogos
                tabelas = soup.find_all("table", class_="tablaPrincipal")
                resultados[campeonato_nome] = []
                for tabela in tabelas:
                    rows = tabela.find_all("tr")
                    dia = None
                    for row in rows:
                        columns = row.find_all("td")
                        dados = [col.text.strip() for col in columns]
                        if len(dados) == 1:  # Caso seja uma linha com o dia
                            dia = dados[0]
                        elif len(dados) >= 5:  # Caso seja uma linha com informações do jogo

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
                            resultados[campeonato_nome].append(jogo)

                # Volta para a página inicial
                page.goto("https://www.futebolaovivobrasil.com/campeonato")
                page.wait_for_selector("ul.listadoEquipos")

            except Exception as e:
                print(f"Erro ao processar o campeonato {campeonato_nome}: {e}")
                page.goto("https://www.futebolaovivobrasil.com/campeonato")
                page.wait_for_selector("ul.listadoEquipos")
                continue

        # Fecha o navegador
        browser.close()

        return resultados


# Chama a função principal
resultados = scrape_website()
for campeonato, jogos in resultados.items():
    print(f"\n{campeonato}:")
    for jogo in jogos:
        print(jogo)
