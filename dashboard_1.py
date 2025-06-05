import dash
from dash import dcc, html, dash_table
import plotly.express as px
import plotly.graph_objs as go
import pandas as pd
import numpy as np

# ==== Dados mock (substitua pelos seus!) ====
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

# MAPAS
fig_mapa_brasil = go.Figure(go.Indicator(mode="number", value=1, title={"text":"Mapa BR (mock)"}))
fig_mapa_rj = go.Figure(go.Indicator(mode="number", value=1, title={"text":"Mapa RJ (mock)"}))

# Gráficos de setores (pizza)
fig_pie_regiao = px.pie(
    values=[100,200,150,300,180],
    names=["Norte","Nordeste","Centro-Oeste","Sudeste","Sul"],
    title="Casos por Região (%)"
)
fig_pie_sudeste = px.pie(
    values=[100,120,95,45],
    names=["RJ","SP","MG","ES"],
    title="Casos Sudeste (%)"
)

# Gráficos linha/casos diários
dias = list(range(1,31))
fig_casos_dia = px.line(pd.DataFrame({
    "dia": dias*2,
    "casos": list(np.random.randint(500,1000,30)) + list(np.random.randint(100,500,30)),
    "entidade": ["Brasil"]*30 + ["RJ"]*30,
}), x="dia", y="casos", color="entidade", markers=True, title="Casos Novos por Dia")

fig_media_obitos = px.line(pd.DataFrame({
    "dia": dias*2,
    "media_movel": list(np.random.uniform(100,400,30)) + list(np.random.uniform(20,100,30)),
    "entidade": ["Brasil"]*30 + ["RJ"]*30,
}), x="dia", y="media_movel", color="entidade", markers=True, title="Média Móvel de Óbitos")

fig_acumulados_rj = go.Figure()
fig_acumulados_rj.add_trace(go.Scatter(x=dias, y=np.cumsum(np.random.randint(100,200,30)), mode='lines+markers', name="Casos", line=dict(color="blue")))
fig_acumulados_rj.add_trace(go.Scatter(x=dias, y=np.cumsum(np.random.randint(10,20,30)), mode='lines+markers', name="Óbitos", line=dict(color="red")))
fig_acumulados_rj.update_layout(title="Casos e Óbitos Acumulados RJ", xaxis_title="Dia", yaxis_title="Total Acumulado")

# ==== Layout ====
app = dash.Dash(__name__, suppress_callback_exceptions=True)
app.layout = html.Div([
    dcc.Tabs([
        dcc.Tab(label="Painel Geral", children=[
            html.Div([
                # Indicadores em 4 colunas
                html.Div([
                    html.Div([
                        html.H5("Total de casos confirmados"),
                        html.Ul([
                            html.Li(f"Brasil: {indicadores['casos_brasil']}", style={"color":"blue"}),
                            html.Li(f"Estado do Rio de Janeiro: {indicadores['casos_rj']}", style={"color":"blue"}),
                            html.Li(f"Cidade do Rio de Janeiro: {indicadores['casos_mun_rj']}", style={"color":"blue"})
                        ])
                    ], style={"width":"24%","display":"inline-block", "verticalAlign":"top"}),
                    html.Div([
                        html.H5("Total de óbitos"),
                        html.Ul([
                            html.Li(f"Brasil: {indicadores['obitos_brasil']}", style={"color":"orange"}),
                            html.Li(f"Estado do Rio de Janeiro: {indicadores['obitos_rj']}", style={"color":"orange"}),
                            html.Li(f"Cidade do Rio de Janeiro: {indicadores['obitos_mun_rj']}", style={"color":"orange"})
                        ])
                    ], style={"width":"24%","display":"inline-block", "verticalAlign":"top"}),
                    html.Div([
                        html.H5("Letalidade (óbitos / casos confirmados)"),
                        html.Ul([
                            html.Li(f"Brasil: {indicadores['letalidade_brasil']}", style={"color":"purple"}),
                            html.Li(f"Estado do Rio de Janeiro: {indicadores['letalidade_rj']}", style={"color":"purple"}),
                            html.Li(f"Cidade do Rio de Janeiro: {indicadores['letalidade_mun_rj']}", style={"color":"purple"})
                        ])
                    ], style={"width":"24%","display":"inline-block", "verticalAlign":"top"}),
                    html.Div([
                        html.H5("Mortalidade (óbitos / habitantes)"),
                        html.Ul([
                            html.Li(f"Brasil: {indicadores['mortalidade_brasil']}", style={"color":"red"}),
                            html.Li(f"Estado do Rio de Janeiro: {indicadores['mortalidade_rj']}", style={"color":"red"}),
                            html.Li(f"Cidade do Rio de Janeiro: {indicadores['mortalidade_mun_rj']}", style={"color":"red"})
                        ])
                    ], style={"width":"24%","display":"inline-block", "verticalAlign":"top"}),
                ], style={"width":"100%","marginBottom":"10px"}),
                # Segunda linha: 3 colunas (mapas, gráficos setores, tabelas)
                html.Div([
                    html.Div([
                        html.Div([
                            html.H6("Casos no Brasil"),
                            dcc.Graph(figure=fig_mapa_brasil, config={"displayModeBar": False}, style={"height":"180px"}),
                        ]),
                        html.Div([
                            html.H6("Casos no Estado do Rio de Janeiro"),
                            dcc.Graph(figure=fig_mapa_rj, config={"displayModeBar": False}, style={"height":"180px"}),
                        ]),
                    ], style={"width":"33%","display":"inline-block","verticalAlign":"top"}),
                    html.Div([
                        html.Div([
                            html.H6("Casos por região"),
                            dcc.Graph(figure=fig_pie_regiao, config={"displayModeBar": False}, style={"height":"180px"}),
                        ]),
                        html.Div([
                            html.H6("Casos por estados da região Sudeste"),
                            dcc.Graph(figure=fig_pie_sudeste, config={"displayModeBar": False}, style={"height":"180px"}),
                        ]),
                    ], style={"width":"33%","display":"inline-block","verticalAlign":"top"}),
                    html.Div([
                        html.Div([
                            html.H6("10 cidades do Brasil com maior taxa de casos confirmados"),
                            dash_table.DataTable(data=df_top_mun_brasil.to_dict("records"),
                                columns=[{"name": i, "id": i} for i in df_top_mun_brasil.columns],
                                style_table={"height":"180px","overflowY":"auto"},
                                page_size=5
                            )
                        ]),
                        html.Div([
                            html.H6("10 cidades do Estado do RJ com maior taxa de casos confirmados"),
                            dash_table.DataTable(data=df_top_mun_rj.to_dict("records"),
                                columns=[{"name": i, "id": i} for i in df_top_mun_rj.columns],
                                style_table={"height":"180px","overflowY":"auto"},
                                page_size=5
                            )
                        ]),
                    ], style={"width":"33%","display":"inline-block","verticalAlign":"top"}),
                ], style={"width":"100%"}),
            ], style={"padding":"10px"})
        ]),
        dcc.Tab(label="Painel de Casos Diários", children=[
            html.Div([
                html.Div([
                    html.Div([
                        html.H6("Casos novos por dia"),
                        dcc.Graph(figure=fig_casos_dia)
                    ]),
                    html.Div([
                        html.H6("Média móvel de óbitos do Brasil e do Estado do Rio de Janeiro"),
                        dcc.Graph(figure=fig_media_obitos)
                    ]),
                    html.Div([
                        html.H6("Casos acumulados e óbitos do Estado do Rio de Janeiro"),
                        dcc.Graph(figure=fig_acumulados_rj)
                    ]),
                ], style={"width":"65%","display":"inline-block","verticalAlign":"top"}),
                html.Div([
                    html.H6("Casos por Estado"),
                    dash_table.DataTable(data=df_estados.to_dict("records"),
                        columns=[{"name": i, "id": i} for i in df_estados.columns],
                        style_table={"height":"700px","overflowY":"auto"},
                        page_size=10
                    )
                ], style={"width":"34%","display":"inline-block","verticalAlign":"top", "marginLeft":"1%"}),
            ], style={"padding":"10px"})
        ])
    ])
])

if __name__ == "__main__":
    app.run(debug=True)
