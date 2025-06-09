# 📦 IMPORTAÇÕES
import sqlite3
import pandas as pd
import geopandas as gpd
from dash import Dash, html, dcc
import dash_bootstrap_components as dbc
from dash import dash_table
import plotly.express as px

# ✅ CONEXÃO COM BANCO E CARREGAMENTO DE DADOS
conn = sqlite3.connect("Data/G2.db")
casos_municipais = pd.read_sql("SELECT * FROM CasosMunicipais", conn)
municipios = pd.read_sql("SELECT * FROM Municipio", conn)
estados = pd.read_sql("SELECT * FROM Estado", conn)
regioes = pd.read_sql("SELECT * FROM Regiao", conn)
conn.close()

# 🔗 MERGE COMPLETO
casos_completos = casos_municipais.merge(municipios, on="codigomunicipal") \
                                   .merge(estados, on="codigoestadual") \
                                   .merge(regioes, on="codigoregiao")
casos_completos["data"] = pd.to_datetime(casos_completos["data"])

# 🔢 CÁLCULOS DE RESUMO
brasil = casos_completos.copy()
rj = casos_completos[casos_completos["uf"] == "RJ"]
mun_rj = casos_completos[casos_completos["codigomunicipal"] == "3304557"]

def resumo_area(df, pop):
    casos = df["casosnovos"].sum()
    obitos = df["mortesnovas"].sum()
    return {
        "casos": casos,
        "obitos": obitos,
        "letalidade": round(obitos / casos * 100, 2) if casos else 0,
        "mortalidade": round(obitos / pop * 100000, 2) if pop else 0
    }

pop_brasil = estados["populacao"].sum()
pop_rj = estados.query("uf == 'RJ'")["populacao"].values[0]
pop_mun_rj = municipios.query("codigomunicipal == '3304557'")["populacao"].values[0]

resumo = {
    "brasil": resumo_area(brasil, pop_brasil),
    "rj": resumo_area(rj, pop_rj),
    "rio": resumo_area(mun_rj, pop_mun_rj)
}

# 🏙️ TABELAS
top_brasil = (
    casos_completos.groupby(["codigomunicipal", "nomecidade", "uf", "populacao_x"], as_index=False)
    .agg({"casosnovos": "sum", "mortesnovas": "sum"})
    .assign(
        Taxa=lambda df: df["casosnovos"] / df["populacao_x"],
        Letalidade=lambda df: df["mortesnovas"] / df["casosnovos"],
        Mortalidade=lambda df: df["mortesnovas"] / df["populacao_x"]
    )
    .sort_values("Taxa", ascending=False)
    .head(10)[["uf", "nomecidade", "Taxa", "Letalidade", "Mortalidade"]]
    .rename(columns={"uf": "UF", "nomecidade": "Nome"})
)

top_rj = (
    rj.groupby(["codigomunicipal", "nomecidade", "populacao_x"], as_index=False)
    .agg({"casosnovos": "sum", "mortesnovas": "sum"})
    .assign(
        Taxa=lambda df: df["casosnovos"] / df["populacao_x"],
        Letalidade=lambda df: df["mortesnovas"] / df["casosnovos"],
        Mortalidade=lambda df: df["mortesnovas"] / df["populacao_x"]
    )
    .sort_values("Taxa", ascending=False)
    .head(10)[["nomecidade", "Taxa", "Letalidade", "Mortalidade"]]
    .rename(columns={"nomecidade": "Nome"})
)

# 📊 GERAÇÃO DOS GRÁFICOS
df_brasil = brasil.groupby("data", as_index=False).agg({"casosnovos": "sum"}).rename(columns={"casosnovos": "casos"})
df_brasil["entidade"] = "Brasil"
df_rj = rj.groupby("data", as_index=False).agg({"casosnovos": "sum"}).rename(columns={"casosnovos": "casos"})
df_rj["entidade"] = "RJ"
df_casos_dia = pd.concat([df_brasil, df_rj])
df_casos_dia["dia"] = df_casos_dia.groupby("entidade").cumcount() + 1

fig_casos_dia = px.line(df_casos_dia, x="dia", y="casos", color="entidade", markers=True,
                        title="Casos Novos por Dia – Brasil vs RJ")

df_obitos_br = brasil.groupby("data", as_index=False).agg({"mortesnovas": "sum"}).rename(columns={"mortesnovas": "obitos"})
df_obitos_br["entidade"] = "Brasil"
df_obitos_rj = rj.groupby("data", as_index=False).agg({"mortesnovas": "sum"}).rename(columns={"mortesnovas": "obitos"})
df_obitos_rj["entidade"] = "RJ"
df_obitos = pd.concat([df_obitos_br, df_obitos_rj])
df_obitos["media_movel"] = df_obitos.groupby("entidade")["obitos"].rolling(window=6, min_periods=1).mean().reset_index(0, drop=True)
df_obitos["dia"] = df_obitos.groupby("entidade").cumcount() + 1

fig_media_obitos = px.line(df_obitos, x="dia", y="media_movel", color="entidade", markers=True,
                           title="Média Móvel de Óbitos – Brasil vs RJ")

df_acum_rj = rj.groupby("data", as_index=False).agg({"casosnovos": "sum", "mortesnovas": "sum"})
df_acum_rj["casos_acumulados"] = df_acum_rj["casosnovos"].cumsum()
df_acum_rj["obitos_acumulados"] = df_acum_rj["mortesnovas"].cumsum()
df_acum_rj["dia"] = range(1, len(df_acum_rj) + 1)

fig_acum = px.line(df_acum_rj, x="dia", y=["casos_acumulados", "obitos_acumulados"],
                   title="Casos e Óbitos Acumulados no Estado do RJ")

# 🌍 MAPAS
shape_brasil = gpd.read_file("Mapas/BR_UF_2022.shp")
mapa_rj = gpd.read_file("Mapas/RJ_Municipios_2022.shp")

casos_estado = casos_completos.groupby("uf", as_index=False).agg({"casosnovos": "sum"}).rename(columns={"casosnovos": "casos_total"})
shape_brasil_dados = shape_brasil.merge(casos_estado, left_on="SIGLA_UF", right_on="uf")

casos_municipio_rj = rj.groupby("codigomunicipal", as_index=False).agg({"casosnovos": "sum"}).rename(columns={"casosnovos": "casos_total"})
mapa_rj_dados = mapa_rj.merge(casos_municipio_rj, left_on="CD_MUN", right_on="codigomunicipal")

fig_mapa_uf = px.choropleth(shape_brasil_dados,
                            geojson=shape_brasil_dados.geometry,
                            locations=shape_brasil_dados.index,
                            color="casos_total",
                            hover_name="NM_UF",
                            title="Casos Confirmados por Estado – Brasil",
                            scope="south america")

fig_mapa_rj = px.choropleth(mapa_rj_dados,
                            geojson=mapa_rj_dados.geometry,
                            locations=mapa_rj_dados.index,
                            color="casos_total",
                            hover_name="NM_MUN",
                            title="Casos Confirmados por Município – RJ")

# 🎨 DASHBOARD COM LAYOUT
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

def bloco_resumo(titulo, dados, cor):
    return dbc.Card([
        dbc.CardBody([
            html.H5(titulo),
            html.P(f"Casos: {dados['casos']:,}"),
            html.P(f"Óbitos: {dados['obitos']:,}"),
            html.P(f"Letalidade: {dados['letalidade']}%"),
            html.P(f"Mortalidade: {dados['mortalidade']} por 100 mil")
        ])
    ], color=cor, inverse=True)

app.layout = dbc.Container([
    html.H2("Painel COVID-19 - Brasil / RJ / Município do RJ", className="my-4 text-center"),

    dbc.Row([
        dbc.Col(bloco_resumo("🇧🇷 Brasil", resumo["brasil"], "primary"), md=3),
        dbc.Col(bloco_resumo("🟦 Estado RJ", resumo["rj"], "info"), md=3),
        dbc.Col(bloco_resumo("🏙️ Município RJ", resumo["rio"], "secondary"), md=3)
    ]),

    html.Hr(),
    dcc.Graph(figure=fig_casos_dia),
    dcc.Graph(figure=fig_media_obitos),
    dcc.Graph(figure=fig_acum),
    dcc.Graph(figure=fig_mapa_uf),
    dcc.Graph(figure=fig_mapa_rj),

    html.H4("Top 10 Cidades do Brasil com Maior Taxa de Casos Confirmados"),
    dash_table.DataTable(
        data=top_brasil.to_dict("records"),
        columns=[{"name": col, "id": col} for col in top_brasil.columns],
        style_table={"overflowX": "auto"},
        style_cell={"textAlign": "left"},
        style_header={"fontWeight": "bold"}
    ),

    html.H4("Top 10 Cidades do RJ com Maior Taxa de Casos Confirmados"),
    dash_table.DataTable(
        data=top_rj.to_dict("records"),
        columns=[{"name": col, "id": col} for col in top_rj.columns],
        style_table={"overflowX": "auto"},
        style_cell={"textAlign": "left"},
        style_header={"fontWeight": "bold"}
    )
], fluid=True)

if __name__ == "__main__":
    app.run(debug=True)
