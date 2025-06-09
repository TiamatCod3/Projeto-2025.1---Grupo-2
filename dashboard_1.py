import dash
from dash import dcc, html, dash_table
import plotly.express as px
import plotly.graph_objs as go
import pandas as pd
import numpy as np


indicadores = {
    "casos_brasil": "12.345.678",
    "casos_rj": "2.345.678",
    "casos_mun_rj": "567.890",
    "obitos_brasil": "234.567",
    "obitos_rj": "45.678",
    "obitos_mun_rj": "12.345",
    "letalidade_brasil": "2,0%",
    "letalidade_rj": "2,3%",
    "letalidade_mun_rj": "2,5%",
    "mortalidade_brasil": "0,8%",
    "mortalidade_rj": "0,9%",
    "mortalidade_mun_rj": "1,0%",
}

df_top_mun_brasil = pd.DataFrame({
    "UF": ["RJ"]*10,
    "Nome": [f"Cidade_{i}" for i in range(1, 11)],
    "Taxa": [round(x,3) for x in np.random.uniform(0.1,2.5,10)],
    "Letalidade": [round(x,2) for x in np.random.uniform(1,4,10)],
    "Mortalidade": [round(x,2) for x in np.random.uniform(0.1,1,10)],
})
df_top_mun_rj = pd.DataFrame({
    "Nome": [f"CidadeRJ_{i}" for i in range(1, 11)],
    "Taxa": [round(x,3) for x in np.random.uniform(0.1,2.5,10)],
    "Letalidade": [round(x,2) for x in np.random.uniform(1,4,10)],
    "Mortalidade": [round(x,2) for x in np.random.uniform(0.1,1,10)],
})
df_estados = pd.DataFrame({
    "UF": ["RJ", "SP", "MG", "ES"],
    "Confirmado": [200000, 300000, 150000, 50000],
    "Obitos": [10000, 12000, 8000, 2000],
    "Letalidade": [5, 4, 5.3, 4],
    "Mortalidade": [0.5, 0.4, 0.53, 0.3],
})

#Mock de dados para regiões (substitua pelos reais se tiver)
regioes = ["Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul"]
casos_regiao = [100_000, 200_000, 150_000, 300_000, 180_000]  # Casos confirmados
populacao_regiao = [18_430_980, 57_374_243, 16_707_336, 89_632_957, 30_377_353]  # População estimada

# Calcula o percentual de casos
pct_regiao = [100 * casos/pop for casos, pop in zip(casos_regiao, populacao_regiao)]

df_regiao = pd.DataFrame({
    "Região": regioes,
    "Percentual de Casos (%)": pct_regiao
})

# Mock para Sudeste (dados fictícios)
estados_sudeste = ["RJ", "SP", "MG", "ES"]
casos_sudeste = [100_000, 120_000, 95_000, 45_000]
populacao_sudeste = [17_264_943, 44_411_238, 21_292_666, 4_064_052]
pct_sudeste = [100 * casos/pop for casos, pop in zip(casos_sudeste, populacao_sudeste)]

df_sudeste = pd.DataFrame({
    "Estado": estados_sudeste,
    "Percentual de Casos (%)": pct_sudeste
})

dias = list(range(1,31))
fig_mapa_brasil = go.Figure(go.Indicator(mode="number", value=1, title={"text":"Mapa BR (mock)"}))
fig_mapa_rj = go.Figure(go.Indicator(mode="number", value=1, title={"text":"Mapa RJ (mock)"}))
fig_bar_regiao = px.bar(
    df_regiao,
    y="Região",
    x="Percentual de Casos (%)",
    orientation="h",
    color="Região",
    title="Percentual de Casos Confirmados por Região (%)",
    text=df_regiao["Percentual de Casos (%)"].map("{:.2f}%".format)
)
fig_bar_regiao.update_layout(showlegend=False, height=220, margin=dict(l=40, r=10, t=40, b=20))
fig_bar_regiao.update_traces(textposition='outside')

fig_bar_sudeste = px.bar(
    df_sudeste,
    y="Estado",
    x="Percentual de Casos (%)",
    orientation="h",
    color="Estado",
    title="Percentual de Casos Confirmados por Estado da Região Sudeste (%)",
    text=df_sudeste["Percentual de Casos (%)"].map("{:.2f}%".format)
)
fig_bar_sudeste.update_layout(showlegend=False, height=180, margin=dict(l=40, r=10, t=40, b=20))
fig_bar_sudeste.update_traces(textposition='outside')


fig_casos_dia = px.line(pd.DataFrame({
    "dia": dias*2,
    "casos": list(np.random.randint(500,1000,30)) + list(np.random.randint(100,500,30)),
    "entidade": ["Brasil"]*30 + ["RJ"]*30,
}), x="dia", y="casos", color="entidade", markers=True)
fig_casos_dia.update_layout(
    margin=dict(l=20, r=10, t=25, b=25),   # Margens mínimas!
    title="",                              # Sem título grande
    legend=dict(
        orientation="h",                   # Legenda horizontal
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1
    )
)
fig_media_obitos = px.line(pd.DataFrame({
    "dia": dias*2,
    "media_movel": list(np.random.uniform(100,400,30)) + list(np.random.uniform(20,100,30)),
    "entidade": ["Brasil"]*30 + ["RJ"]*30,
}), x="dia", y="media_movel", color="entidade", markers=True)
fig_media_obitos.update_layout(
    margin=dict(l=20, r=10, t=25, b=25),   # Margens mínimas!
    title="",                              # Sem título grande
    legend=dict(
        orientation="h",                   # Legenda horizontal
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1
    )
)
fig_acumulados_rj = go.Figure()
fig_acumulados_rj.add_trace(go.Scatter(x=dias, y=np.cumsum(np.random.randint(100,200,30)), mode='lines+markers', name="Casos", line=dict(color="blue")))
fig_acumulados_rj.add_trace(go.Scatter(x=dias, y=np.cumsum(np.random.randint(10,20,30)), mode='lines+markers', name="Óbitos", line=dict(color="red")))
fig_acumulados_rj.update_layout(
    margin=dict(l=20, r=10, t=25, b=25),   # Margens mínimas!
    title="",                              # Sem título grande
    legend=dict(
        orientation="h",                   # Legenda horizontal
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1
    )
)


# ================== DASH APP LAYOUT =====================
caixa_kpi_style = {
    "border": "2px solid #0074D9",
    "borderRadius": "20px",
    "padding": "6px 8px",
    "margin": "2px",
    "background": "#fff",
    "boxSizing": "border-box",
    "minHeight": "80px",
    "flex": "1 1 0",  # Permite flexibilidade e quebra de linha
    "whiteSpace": "normal",
    "overflow": "hidden",
    "display": "flex",
    "flexDirection": "column",
    "justifyContent": "center"
}

# Define a altura desejada para os gráficos/mapas/tabelas para manter alinhamento
altura_mapa = "170px"
altura_grafico = "120px"
altura_tabela = "120px"
caixa_coluna_style = {
    "border": "2px solid #0074D9",
    "borderRadius": "20px",
    "padding": "10px 10px",
    "margin": "2px",
    "background": "#fff",
    "boxSizing": "border-box",
    "minHeight": "100px",
    "display": "flex",
    "flexDirection": "column",
    "justifyContent": "flex-start",
    "width": "32%"
}

kpi_title = {"marginBottom": "1px", "fontSize": "15px"}
kpi_li_style = {"marginLeft": "6px", "fontSize": "13px", "lineHeight": "1.1"}

caixa_style = {
    "border":"2px solid #0074D9", "borderRadius":"20px",
    "padding":"10px", "margin":"6px", "background":"#fff",
    "boxSizing":"border-box"
}

caixa_style_grafico = {
    "border": "2px solid #0074D9",
    "borderRadius": "20px",
    "background": "#fff",
    "boxSizing": "border-box"
}


altura_grafico_casos = "250px"

app = dash.Dash(__name__, suppress_callback_exceptions=True)
app.title = "INF1514_G2_2_Python_Painel"
app.layout = html.Div([
    html.H2("INF1514_G2_2_Python_Painel", style={"textAlign":"center", "marginTop":"10px"}),


    dcc.Tabs([
        dcc.Tab(label="Painel Geral", children=[
            # ====== KPIs TOP (4 colunas) ======
    html.Div([
        html.Div([
            html.B("Total de casos confirmados"),
            html.Ul([
                html.Li(["Brasil", html.Br(), html.Span(indicadores['casos_brasil'], style={"color":"#0074D9", "fontWeight":"bold"})], style=kpi_li_style),
                html.Li(["Estado do Rio de Janeiro", html.Br(), html.Span(indicadores['casos_rj'], style={"color":"#0074D9", "fontWeight":"bold"})], style=kpi_li_style),
                html.Li(["Cidade do Rio de Janeiro", html.Br(), html.Span(indicadores['casos_mun_rj'], style={"color":"#0074D9", "fontWeight":"bold"})], style=kpi_li_style),
            ])
        ], style={**caixa_kpi_style, "width":"24%", "display":"inline-block", "verticalAlign":"top"}),
        html.Div([
            html.B("Total de óbitos"),
            html.Ul([
                html.Li(["Brasil", html.Br(), html.Span(indicadores['obitos_brasil'], style={"color":"#ff9900", "fontWeight":"bold"})], style=kpi_li_style),
                html.Li(["Estado do Rio de Janeiro", html.Br(), html.Span(indicadores['obitos_rj'], style={"color":"#ff9900", "fontWeight":"bold"})], style=kpi_li_style),
                html.Li(["Cidade do Rio de Janeiro", html.Br(), html.Span(indicadores['obitos_mun_rj'], style={"color":"#ff9900", "fontWeight":"bold"})], style=kpi_li_style),
            ])
        ], style={**caixa_kpi_style, "width":"24%", "display":"inline-block", "verticalAlign":"top"}),
        html.Div([
            html.B("Letalidade ", style=kpi_title),
            html.Span("(total de óbitos / total de casos confirmados)", style={"fontSize":"11px"}),
            html.Ul([
                html.Li(["Brasil", html.Br(), html.Span(indicadores['letalidade_brasil'], style={"color":"#9933ff", "fontWeight":"bold"})], style=kpi_li_style),
                html.Li(["Estado do Rio de Janeiro", html.Br(), html.Span(indicadores['letalidade_rj'], style={"color":"#9933ff", "fontWeight":"bold"})], style=kpi_li_style),
                html.Li(["Cidade do Rio de Janeiro", html.Br(), html.Span(indicadores['letalidade_mun_rj'], style={"color":"#9933ff", "fontWeight":"bold"})], style=kpi_li_style),
            ])
        ], style={**caixa_kpi_style, "width":"24%", "display":"inline-block", "verticalAlign":"top"}),
        html.Div([
            html.B("Mortalidade ", style=kpi_title),
            html.Span("(total de óbitos / total de habitantes)", style={"fontSize":"11px"}),
            html.Ul([
                html.Li(["Brasil", html.Br(), html.Span(indicadores['mortalidade_brasil'], style={"color":"#e60000", "fontWeight":"bold"})], style=kpi_li_style),
                html.Li(["Estado do Rio de Janeiro", html.Br(), html.Span(indicadores['mortalidade_rj'], style={"color":"#e60000", "fontWeight":"bold"})], style=kpi_li_style),
                html.Li(["Cidade do Rio de Janeiro", html.Br(), html.Span(indicadores['mortalidade_mun_rj'], style={"color":"#e60000", "fontWeight":"bold"})], style=kpi_li_style),
            ])
        ], style={**caixa_kpi_style, "width":"24%", "display":"inline-block", "verticalAlign":"top"}),
    ], style={"width":"100%", "marginBottom":"8px"}),

    # ======== LINHA 1 =============
    # LINHA 1 (encaixada)
    html.Div([
    # COLUNA 1: Mapas (um em cima do outro)
    html.Div([
        html.B("Casos no Brasil"),
        dcc.Graph(figure=fig_mapa_brasil, config={"displayModeBar": False}, style={"height": altura_mapa}),
        html.B("Casos no Estado do Rio de Janeiro", style={"marginTop": "10px"}),
        dcc.Graph(figure=fig_mapa_rj, config={"displayModeBar": False}, style={"height": altura_mapa}),
    ], style=caixa_coluna_style),

    # COLUNA 2: Gráficos de setores (um em cima do outro)
    html.Div([
        html.B("Casos por região"),
        dcc.Graph(figure=fig_bar_regiao, config={"displayModeBar": False}, style={"height": altura_grafico}),
        html.B("Casos por estados da região Sudeste", style={"marginTop": "10px"}),
        dcc.Graph(figure=fig_bar_sudeste, config={"displayModeBar": False}, style={"height": altura_grafico}),
    ], style=caixa_coluna_style),

    # COLUNA 3: Tabelas (uma em cima da outra)
    html.Div([
        html.B("10 cidades do Brasil com maior taxa de casos confirmados", style={"fontSize":"14px"}),
        dash_table.DataTable(
            data=df_top_mun_brasil.to_dict("records"),
            columns=[{"name": i, "id": i} for i in df_top_mun_brasil.columns],
            style_table={"height": altura_tabela, "overflowY": "auto"},
            style_cell={"textAlign": "center"},
            page_size=5
        ),
        html.B("10 cidades do Estado do RJ com maior taxa de casos confirmados", style={"fontSize":"14px", "marginTop":"10px"}),
        dash_table.DataTable(
            data=df_top_mun_rj.to_dict("records"),
            columns=[{"name": i, "id": i} for i in df_top_mun_rj.columns],
            style_table={"height": altura_tabela, "overflowY": "auto"},
            style_cell={"textAlign": "center"},
            page_size=5
        ),
    ], style=caixa_coluna_style),

], style={
    "width": "100%",
    "display": "flex",
    "justifyContent": "space-between",
    "marginBottom": "8px"
}),

        ]),
    
        dcc.Tab(label="Painel de Casos Diários", children=[
    


    # ======== PARTE INFERIOR (GRÁFICOS TEMPORAIS E TABELA) ======
    # altura dos gráficos individuais

    html.Div([
    html.Div([
        html.B("Casos novos por dia"),
        dcc.Graph(figure=fig_casos_dia, config={"displayModeBar": False},style={"height": altura_grafico_casos}),
        html.B("Média móvel de óbitos do Brasil e do Estado do RJ"),
        dcc.Graph(figure=fig_media_obitos, config={"displayModeBar": False},style={"height": altura_grafico_casos}),
        html.B("Casos acumulados e óbitos do Estado do RJ"),
        dcc.Graph(figure=fig_acumulados_rj, config={"displayModeBar": False},style={"height": altura_grafico_casos}),
    ], style={
        **caixa_style_grafico,
        "width": "64%",
        "minWidth": "350px",
        "marginRight": "4px",  # Menor margem lateral ainda
        "display": "flex",
        "flexDirection": "column",
        "justifyContent": "flex-start"
    }),
    html.Div([
        html.B("Casos por Estado"),
        dash_table.DataTable(
            data=df_estados.to_dict("records"),
            columns=[{"name": i, "id": i} for i in df_estados.columns],
            style_table={"height": "660px", "overflowY": "auto"},
            style_cell={"textAlign": "center"},
            page_size=10
        ),
    ], style={
        **caixa_style_grafico,
        "width": "35%",
        "minWidth": "290px",
        "maxWidth": "450px",
        "display": "flex",
        "flexDirection": "column",
        "justifyContent": "flex-start"
    }),
], style={
    "width": "100%",
    "display": "flex",
    "flexDirection": "row",
    "alignItems": "flex-start",
    "justifyContent": "space-between",
    "marginBottom": "8px"
})
,
        ]),
    ]),
    

    
], style={"background":"#fff", "padding":"10px"})

if __name__ == "__main__":
    app.run(debug=True)
