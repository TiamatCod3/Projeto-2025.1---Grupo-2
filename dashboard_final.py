import dash
from dash import dcc, html, dash_table
import plotly.express as px
import plotly.graph_objs as go
import pandas as pd
import geopandas as gpd
import numpy as np
import json
import sqlite3

# ======= CONEXÃO E LEITURA DO BANCO ============
conn = sqlite3.connect("Data/G2.db")  # Ajuste o caminho se necessário

df_casos_municipais = pd.read_sql("SELECT * FROM CasosMunicipais", conn)
df_municipios = pd.read_sql("SELECT * FROM Municipio", conn)
df_estados = pd.read_sql("SELECT * FROM Estado", conn)
df_regioes = pd.read_sql("SELECT * FROM Regiao", conn)
conn.close()

# ======= PRÉ-PROCESSAMENTO ==========

# Juntar tabelas
df = df_casos_municipais.merge(df_municipios, on="codigomunicipal", suffixes=("", "_mun"))
df = df.merge(df_estados, on="codigoestadual", suffixes=("", "_est"))
df = df.merge(df_regioes, on="codigoregiao", suffixes=("", "_reg"))

# Para os nomes de colunas, ajuste conforme o seu banco! Exemplos abaixo:
# df['casosnovos'], df['obitos'], df['nomecidade'], df['populacao'], df['nome_est'], df['uf'], df['populacao_est'], df['nome_reg']

# INDICADORES PRINCIPAIS (Brasil, RJ, Município do RJ)
total_casos_brasil = int(df["casosnovos"].sum())
total_obitos_brasil = int(df["mortesnovas"].sum())
pop_brasil = int(df["populacao_est"].unique().sum())  # pop dos estados

letalidade_brasil = 100 * total_obitos_brasil / total_casos_brasil if total_casos_brasil else 0
mortalidade_brasil = 100 * total_obitos_brasil / pop_brasil if pop_brasil else 0

# Estado RJ
df_rj = df[df["uf"] == "RJ"]
total_casos_rj = int(df_rj["casosnovos"].sum())
total_obitos_rj = int(df_rj["mortesnovas"].sum())
pop_rj = int(df_rj["populacao_est"].unique().sum())
letalidade_rj = 100 * total_obitos_rj / total_casos_rj if total_casos_rj else 0
mortalidade_rj = 100 * total_obitos_rj / pop_rj if pop_rj else 0

# Município RJ (Cidade do Rio de Janeiro)
df_mun_rj = df[df["nomecidade"].str.lower().str.contains("rio de janeiro")]

total_casos_mun_rj = int(df_mun_rj["casosnovos"].sum())
total_obitos_mun_rj = int(df_mun_rj["mortesnovas"].sum())
pop_mun_rj = int(df_mun_rj["populacao"].unique().sum())
letalidade_mun_rj = 100 * total_obitos_mun_rj / total_casos_mun_rj if total_casos_mun_rj else 0
mortalidade_mun_rj = 100 * total_obitos_mun_rj / pop_mun_rj if pop_mun_rj else 0

indicadores = {
    "casos_brasil": f"{total_casos_brasil:,}".replace(",", "."),
    "casos_rj": f"{total_casos_rj:,}".replace(",", "."),
    "casos_mun_rj": f"{total_casos_mun_rj:,}".replace(",", "."),
    "obitos_brasil": f"{total_obitos_brasil:,}".replace(",", "."),
    "obitos_rj": f"{total_obitos_rj:,}".replace(",", "."),
    "obitos_mun_rj": f"{total_obitos_mun_rj:,}".replace(",", "."),
    "letalidade_brasil": f"{letalidade_brasil:.2f}%",
    "letalidade_rj": f"{letalidade_rj:.2f}%",
    "letalidade_mun_rj": f"{letalidade_mun_rj:.2f}%",
    "mortalidade_brasil": f"{mortalidade_brasil:.2f}%",
    "mortalidade_rj": f"{mortalidade_rj:.2f}%",
    "mortalidade_mun_rj": f"{mortalidade_mun_rj:.2f}%"
}

# ====== Top 10 cidades Brasil e RJ ======
# Ordenando por taxa de casos confirmados/habitantes
df_cidade_brasil = df.groupby(["uf", "nomecidade"]).agg({
    "casosnovos": "sum",
    "mortesnovas": "sum",
    "populacao": "first"
}).reset_index()
df_cidade_brasil["Taxa"] = df_cidade_brasil["casosnovos"] / df_cidade_brasil["populacao"]
df_cidade_brasil["Letalidade"] = 100 * df_cidade_brasil["mortesnovas"] / df_cidade_brasil["casosnovos"]
df_cidade_brasil["Mortalidade"] = 100 * df_cidade_brasil["mortesnovas"] / df_cidade_brasil["populacao"]
df_top_mun_brasil = df_cidade_brasil.sort_values(["Taxa", "uf", "nomecidade"], ascending=[False, True, True]).head(10)
df_top_mun_brasil = df_top_mun_brasil.rename(columns={"uf": "UF", "nomecidade": "Nome"})
df_top_mun_brasil = df_top_mun_brasil[["UF", "Nome", "Taxa", "Letalidade", "Mortalidade"]]

# Top 10 cidades RJ
df_cidade_rj = df_cidade_brasil[df_cidade_brasil["uf"] == "RJ"]
df_top_mun_rj = df_cidade_rj.sort_values("Taxa", ascending=False).head(10)
df_top_mun_rj = df_top_mun_rj.rename(columns={"uf": "UF", "nomecidade": "Nome"})
df_top_mun_rj = df_top_mun_rj[["Nome", "Taxa", "Letalidade", "Mortalidade"]]

# ====== Casos por Região ======
df_regiao = df.groupby("nomeregiao").agg({
    "casosnovos": "sum",
    "populacao_est": "sum"
}).reset_index()
df_regiao["Percentual de Casos (%)"] = 100 * df_regiao["casosnovos"] / df_regiao["populacao_est"]
df_regiao = df_regiao.rename(columns={"nomeregiao": "Região"})

# # ====== Casos por Estado da Região Sudeste ======
df_sudeste = df[df["nomeregiao"] == "Sudeste"]
df_estado_sudeste = df_sudeste.groupby("uf").agg({
    "casosnovos": "sum",
    "populacao_est": "sum"
}).reset_index()
df_estado_sudeste["Percentual de Casos (%)"] = 100 * df_estado_sudeste["casosnovos"] / df_estado_sudeste["populacao_est"]
df_estado_sudeste = df_estado_sudeste.rename(columns={"uf": "Estado"})

# # ====== Gráficos de Barra ======
fig_bar_regiao = px.bar(
    df_regiao,
    y="Região",
    x="Percentual de Casos (%)",
    orientation="h",
    color="Região",
    text=df_regiao["Percentual de Casos (%)"].map("{:.2f}%".format)
)
fig_bar_regiao.update_layout(showlegend=False, height=220, margin=dict(l=40, r=10, t=40, b=20))
fig_bar_regiao.update_traces(textposition='outside')

fig_bar_sudeste = px.bar(
    df_estado_sudeste,
    y="Estado",
    x="Percentual de Casos (%)",
    orientation="h",
    color="Estado",
    text=df_estado_sudeste["Percentual de Casos (%)"].map("{:.2f}%".format)
)
fig_bar_sudeste.update_layout(showlegend=False, height=180, margin=dict(l=40, r=10, t=40, b=20))
fig_bar_sudeste.update_traces(textposition='outside')

# ====== Casos por Estado ======
df_casos_estado = df.groupby("uf").agg({
    "casosnovos": "sum",
    "mortesnovas": "sum",
    "populacao_est": "sum"
}).reset_index()
df_casos_estado["Letalidade"] = 100 * df_casos_estado["mortesnovas"] / df_casos_estado["casosnovos"]
df_casos_estado["Mortalidade"] = 100 * df_casos_estado["mortesnovas"] / df_casos_estado["populacao_est"]
df_estados_table = df_casos_estado.rename(columns={
    "uf": "UF",
    "casosnovos": "Confirmado",
    "mortesnovas": "Obitos",
    "populacao_est": "População"
})[["UF", "Confirmado", "Obitos", "Letalidade", "Mortalidade"]]

# === MAPAS ===
shp_brasil = gpd.read_file("Mapas/BR_UF_2022.shp")
shp_brasil = shp_brasil.rename(columns={"CD_UF": "codigoibge"})
geojson_brasil = json.loads(shp_brasil.to_json())

mapa_brasil = px.choropleth(
    df_estados_table.merge(shp_brasil, left_on="UF", right_on="SIGLA_UF"),
    geojson=geojson_brasil,
    locations="codigoibge",
    color="Confirmados",
    featureidkey="properties.codigoibge",
    title="Casos Confirmados por Estado – Brasil"
)

shp_rj = gpd.read_file("Mapas/33MUE250GC_SIR.shp")
shp_rj = shp_rj.rename(columns={"CD_MUN": "codigomunicipal"})
geojson_rj = json.loads(shp_rj.to_json())

mapa_rj = px.choropleth(
    casos[casos['uf'] == 'RJ'].groupby('codigomunicipal').agg({'casosnovos': 'sum'}).reset_index().merge(shp_rj, on='codigomunicipal'),
    geojson=geojson_rj,
    locations="codigomunicipal",
    color="casosnovos",
    featureidkey="properties.codigomunicipal",
    title="Casos Confirmados por Município – RJ"
)

# ====== MOCKS PARA TEMPORAIS (use seus dados reais depois) =====
dias = list(range(1, 31))
fig_casos_dia = px.line(pd.DataFrame({
    "dia": dias * 2,
    "casos": list(np.random.randint(500, 1000, 30)) + list(np.random.randint(100, 500, 30)),
    "entidade": ["Brasil"] * 30 + ["RJ"] * 30,
}), x="dia", y="casos", color="entidade", markers=True)
fig_casos_dia.update_layout(
    margin=dict(l=20, r=10, t=25, b=25), title="", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)
fig_media_obitos = px.line(pd.DataFrame({
    "dia": dias * 2,
    "media_movel": list(np.random.uniform(100, 400, 30)) + list(np.random.uniform(20, 100, 30)),
    "entidade": ["Brasil"] * 30 + ["RJ"] * 30,
}), x="dia", y="media_movel", color="entidade", markers=True)
fig_media_obitos.update_layout(
    margin=dict(l=20, r=10, t=25, b=25), title="", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)
fig_acumulados_rj = go.Figure()
fig_acumulados_rj.add_trace(go.Scatter(x=dias, y=np.cumsum(np.random.randint(100, 200, 30)), mode='lines+markers', name="Casos", line=dict(color="blue")))
fig_acumulados_rj.add_trace(go.Scatter(x=dias, y=np.cumsum(np.random.randint(10, 20, 30)), mode='lines+markers', name="Óbitos", line=dict(color="red")))
fig_acumulados_rj.update_layout(
    margin=dict(l=20, r=10, t=25, b=25), title="", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)

# ========== DASH APP LAYOUT ==========

caixa_kpi_style = {
    "border": "2px solid #0074D9",
    "borderRadius": "20px",
    "padding": "6px 8px",
    "margin": "2px",
    "background": "#fff",
    "boxSizing": "border-box",
    "minHeight": "80px",
    "flex": "1 1 0",
    "whiteSpace": "normal",
    "overflow": "hidden",
    "display": "flex",
    "flexDirection": "column",
    "justifyContent": "center"
}

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
    html.H2("INF1514_G2_2_Python_Painel", style={"textAlign": "center", "marginTop": "10px"}),
    dcc.Tabs([
        dcc.Tab(label="Painel Geral", children=[
            # KPIs TOP
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

            # Linha principal com mapas, gráficos e tabelas
            html.Div([
                # COLUNA 1: Mapas
                html.Div([
                    html.B("Casos no Brasil"),
                    dcc.Graph(figure=fig_mapa_brasil, config={"displayModeBar": False}, style={"height": altura_mapa}),
                    html.B("Casos no Estado do Rio de Janeiro", style={"marginTop": "10px"}),
                    dcc.Graph(figure=fig_mapa_rj, config={"displayModeBar": False}, style={"height": altura_mapa}),
                ], style=caixa_coluna_style),

                # COLUNA 2: Gráficos de barras
                html.Div([
                    html.B("Casos por região"),
                    dcc.Graph(figure=fig_bar_regiao, config={"displayModeBar": False}, style={"height": altura_grafico}),
                    html.B("Casos por estados da região Sudeste", style={"marginTop": "10px"}),
                    dcc.Graph(figure=fig_bar_sudeste, config={"displayModeBar": False}, style={"height": altura_grafico}),
                ], style=caixa_coluna_style),

                # COLUNA 3: Tabelas top 10
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

        # PAINEL DE CASOS DIÁRIOS
        dcc.Tab(label="Painel de Casos Diários", children=[
            html.Div([
                html.Div([
                    html.B("Casos novos por dia"),
                    dcc.Graph(figure=fig_casos_dia, config={"displayModeBar": False}, style={"height": "250px"}),
                    html.B("Média móvel de óbitos do Brasil e do Estado do RJ"),
                    dcc.Graph(figure=fig_media_obitos, config={"displayModeBar": False}, style={"height": "250px"}),
                    html.B("Casos acumulados e óbitos do Estado do RJ"),
                    dcc.Graph(figure=fig_acumulados_rj, config={"displayModeBar": False}, style={"height": "250px"}),
                ], style={
                    **caixa_style_grafico,
                    "width": "64%",
                    "minWidth": "350px",
                    "marginRight": "4px",
                    "display": "flex",
                    "flexDirection": "column",
                    "justifyContent": "flex-start"
                }),
                html.Div([
                    html.B("Casos por Estado"),
                    dash_table.DataTable(
                        data=df_estados_table.to_dict("records"),
                        columns=[{"name": i, "id": i} for i in df_estados_table.columns],
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
        ]),
    ]),
], style={"background": "#fff", "padding": "10px"})

if __name__ == "__main__":
    app.run(debug=True)
