# -*- coding: utf-8 -*-

# Importando as bibliotecas necessárias
import dash
import dash_bootstrap_components as dbc
from dash import html
from dash.dependencies import Input, Output

# --- Inicialização da Aplicação Dash ---
# Usamos o tema BOOTSTRAP para um design limpo e responsivo.
# A meta tag de viewport é adicionada para garantir a responsividade em dispositivos móveis.
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP],
                meta_tags=[{'name': 'viewport',
                            'content': 'width=device-width, initial-scale=1.0'}])
app.title = "Painel de Monitoramento"
server = app.server


# --- Definição dos Placeholders (Textos de exemplo) ---
# Usamos esta abordagem para não poluir o layout com textos longos e repetitivos.
placeholder_texts = {
    "mapa_brasil": "<Mapa do Brasil por estados com padrão de cor degradê baseado no total de casos confirmados até o momento.>",
    "mapa_rj": "<Mapa do RJ por cidades com padrão de cor degradê baseado no total de casos confirmados até o momento>",
    "grafico_regiao": "<Gráfico de setores por região do Brasil com o % de casos confirmados (acumulados) de cada região. O gráfico deverá apresentar legenda.>",
    "grafico_sudeste": "<Gráfico de setores por estados e % do total de casos confirmados (acumulados) de cada um com legenda.>",
    "tabela_brasil": "<Tabela com 5 colunas: UF, Nome, Taxa, Letalidade e Mortalidade. Os valores devem tomar como base o total de casos acumulados...>",
    "tabela_rj": "<Tabela com 4 colunas: Nome, Taxa, Letalidade e Mortalidade. Os valores devem tomar como base o total de casos acumulados...>",
    "grafico_casos_novos": "<Gráfico de dispersão, tendo os pontos ligados, com o eixo X representando os dias e o eixo Y o total de casos novos...>",
    "grafico_media_movel": "<Gráfico de dispersão formado pela média móvel com uma janela de 6 dias (dia atual + 5 anteriores) do total de óbitos...>",
    "grafico_acumulados": "<Gráfico de dispersão, tendo os pontos ligados, com o eixo X representando os dias e o eixo Y o total de casos acumulados e o total de óbitos acumulados...>",
    "tabela_estados": "<Tabela com 5 colunas: UF do estado, Confirmado, Óbitos, Letalidade e Mortalidade. Os valores devem tomar como base o total de casos acumulados...>"
}


# --- Funções para criar componentes reutilizáveis ---

def create_metric_card(title, items):
    """Cria um card de métrica com título e uma lista de itens."""
    return dbc.Card(
        dbc.CardBody([
            html.H4(title, className="card-title"),
            html.Ul([
                html.Li([
                    item, html.Br(), html.Span("<XXX>", className="placeholder-text")
                ]) for item in items
            ], className="list-unstyled")
        ]),
        className="info-card h-100"
    )

def create_content_card(title, placeholder_key, extra_content=None):
    """Cria um card de conteúdo genérico com título e placeholder."""
    children = [
        html.H4(title, className="card-title"),
        html.P(placeholder_texts[placeholder_key], className="placeholder-text card-content")
    ]
    if extra_content:
        children.extend(extra_content)
    return dbc.Card(dbc.CardBody(children), className="info-card h-100")


# --- Layout da Página 1 ---
page_1_layout = html.Div([
    # Linha de Métricas
    dbc.Row([
        dbc.Col(create_metric_card("Total de casos confirmados", ["Brasil", "Estado do Rio de Janeiro", "Cidade do Rio de Janeiro"]), lg=3, md=6, className="mb-4"),
        dbc.Col(create_metric_card("Total de óbitos", ["Brasil", "Estado do Rio de Janeiro", "Cidade do Rio de Janeiro"]), lg=3, md=6, className="mb-4"),
        dbc.Col(create_metric_card("Letalidade (...)", ["Brasil", "Estado do Rio de Janeiro", "Cidade do Rio de Janeiro"]), lg=3, md=6, className="mb-4"),
        dbc.Col(create_metric_card("Mortalidade (...)", ["Brasil", "Estado do Rio de Janeiro", "Cidade do Rio de Janeiro"]), lg=3, md=6, className="mb-4"),
    ]),
    # Grid Principal de Conteúdo
    dbc.Row([
        # Coluna 1: Mapas
        dbc.Col(
            create_content_card("Casos no Brasil", "mapa_brasil", extra_content=[
                html.Hr(className="my-4"),
                html.H4("Casos no Estado do Rio de Janeiro", className="card-title"),
                html.P(placeholder_texts["mapa_rj"], className="placeholder-text card-content")
            ]),
            lg=4, className="mb-4 d-flex flex-column"
        ),
        # Coluna 2: Gráficos de Setores
        dbc.Col(
            create_content_card("Casos por região", "grafico_regiao", extra_content=[
                html.Hr(className="my-4"),
                html.H4("Casos por estados da região Sudeste", className="card-title"),
                html.P(placeholder_texts["grafico_sudeste"], className="placeholder-text card-content")
            ]),
            lg=4, className="mb-4 d-flex flex-column"
        ),
        # Coluna 3: Tabelas
        dbc.Col([
            dbc.Card(dbc.CardBody([
                html.H4("10 cidades do Brasil com maior taxa de casos confirmados", className="card-title"),
                html.P(placeholder_texts["tabela_brasil"], className="placeholder-text card-content")
            ]), className="info-card mb-4 flex-grow-1"),
            dbc.Card(dbc.CardBody([
                html.H4("10 cidades do Estado do RJ com maior taxa de casos confirmados", className="card-title"),
                html.P(placeholder_texts["tabela_rj"], className="placeholder-text card-content")
            ]), className="info-card flex-grow-1"),
        ], lg=4, className="mb-4 d-flex flex-column"),
    ], className="flex-grow-1"),
], className="d-flex flex-column flex-grow-1")


# --- Layout da Página 2 ---
page_2_layout = html.Div([
    dbc.Row([
        # Coluna Esquerda: Gráficos Empilhados
        dbc.Col([
            dbc.Card(dbc.CardBody([
                html.H4("Casos novos por dia", className="card-title"),
                html.P(placeholder_texts["grafico_casos_novos"], className="placeholder-text card-content")
            ]), className="info-card mb-4 flex-grow-1"),
            dbc.Card(dbc.CardBody([
                html.H4("Média móvel de óbitos do Brasil e do Estado do Rio de Janeiro", className="card-title"),
                html.P(placeholder_texts["grafico_media_movel"], className="placeholder-text card-content")
            ]), className="info-card mb-4 flex-grow-1"),
            dbc.Card(dbc.CardBody([
                html.H4("Casos acumulados e óbitos do Estado do Rio de Janeiro", className="card-title"),
                html.P(placeholder_texts["grafico_acumulados"], className="placeholder-text card-content")
            ]), className="info-card flex-grow-1"),
        ], lg=6, className="d-flex flex-column mb-4"),

        # Coluna Direita: Tabela única
        dbc.Col(
            create_content_card("Casos por Estado", "tabela_estados"),
            lg=6, className="d-flex flex-column mb-4"
        ),
    ], className="flex-grow-1"),
], className="d-flex flex-column flex-grow-1")


# --- Layout Principal da Aplicação ---
app.layout = html.Div([
    # Navegação
    dbc.NavbarSimple(
        children=[
            dbc.ButtonGroup([
                dbc.Button("Página 1", id="btn-page1", color="primary", className="me-1"),
                dbc.Button("Página 2", id="btn-page2", color="secondary", className="me-1"),
            ])
        ],
        brand="Dashboard de Monitoramento",
        brand_href="#",
        color="dark",
        dark=True,
        className="mb-4"
    ),
    # Container para renderizar o conteúdo da página selecionada
    dbc.Container(id="page-content", fluid=True, className="flex-grow-1 d-flex flex-column")
], className="d-flex flex-column vh-100")


# --- Callback para trocar de página ---
@app.callback(
    Output("page-content", "children"),
    Output("btn-page1", "color"),
    Output("btn-page2", "color"),
    Input("btn-page1", "n_clicks"),
    Input("btn-page2", "n_clicks")
)
def display_page(n1, n2):
    # dash.callback_context nos permite saber qual botão foi clicado
    ctx = dash.callback_context
    if not ctx.triggered:
        # Estado inicial, carrega a página 1
        return page_1_layout, "primary", "secondary"
    
    button_id = ctx.triggered[0]["prop_id"].split(".")[0]
    
    if button_id == "btn-page2":
        return page_2_layout, "secondary", "primary"
    else:
        return page_1_layout, "primary", "secondary"

# --- Execução da Aplicação ---
if __name__ == "__main__":
    app.run(debug=True)
