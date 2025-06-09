# 📦 Importações
import pandas as pd
import sqlite3
import numpy as np
import geopandas as gpd
import json
import plotly.express as px
from dash import Dash, html, dcc, dash_table

# 🔌 Conectar ao banco
conn = sqlite3.connect("Data/G2.db")
casos_municipais = pd.read_sql_query("SELECT * FROM CasosMunicipais", conn)
municipios = pd.read_sql_query("SELECT * FROM Municipio", conn)
estados = pd.read_sql_query("SELECT * FROM Estado", conn)
regioes = pd.read_sql_query("SELECT * FROM Regiao", conn)
conn.close()

# 🔗 Juntar tabelas
casos = casos_municipais.merge(municipios, on='codigomunicipal') \
                        .merge(estados, on='codigoestadual') \
                        .merge(regioes, on='codigoregiao')
casos['data'] = pd.to_datetime(casos['data'], dayfirst=True)
casos['casosnovos'] = casos['casosnovos'].fillna(0)
casos['mortesnovas'] = casos['mortesnovas'].fillna(0)

# ======== Blocos de agregação (exemplos) ========
# 1. Casos por Estado
casos_estado = casos.groupby(['uf', 'codigoibge']).agg({
    'casosnovos': 'sum',
    'mortesnovas': 'sum'
}).reset_index().rename(columns={'casosnovos': 'Confirmados', 'mortesnovas': 'Óbitos'})

# 2. Casos por Região
casos_regiao = casos.groupby('nomeregiao').agg({
    'casosnovos': 'sum',
    'populacao_est': 'sum'
}).reset_index()
casos_regiao['taxa_casos_100k'] = 100000 * casos_regiao['casosnovos'] / casos_regiao['populacao_est']

# 3. Casos por Estado da Sudeste
casos_sudeste = casos[casos['nomeregiao'] == 'Sudeste'].groupby('uf').agg({
    'casosnovos': 'sum',
    'populacao_est': 'sum'
}).reset_index()
casos_sudeste['taxa_casos_100k'] = 100000 * casos_sudeste['casosnovos'] / casos_sudeste['populacao_est']

# 4. Top 10 cidades Brasil
top10_brasil = casos.groupby('nomecidade').agg({
    'casosnovos': 'sum',
    'populacao': 'first'
}).reset_index()
top10_brasil['taxa_casos_100k'] = 100000 * top10_brasil['casosnovos'] / top10_brasil['populacao']
top10_brasil = top10_brasil.sort_values('taxa_casos_100k', ascending=False).head(10)

# 5. Top 10 cidades RJ
top10_rj = casos[casos['uf'] == 'RJ'].groupby('nomecidade').agg({
    'casosnovos': 'sum',
    'populacao': 'first'
}).reset_index()
top10_rj['taxa_casos_100k'] = 100000 * top10_rj['casosnovos'] / top10_rj['populacao']
top10_rj = top10_rj.sort_values('taxa_casos_100k', ascending=False).head(10)

# 6. Casos diários
casos_dia = casos.groupby(['data']).agg({
    'casosnovos': 'sum'
}).reset_index().rename(columns={'casosnovos': 'Brasil'})
casos_dia['RJ'] = casos[casos['uf'] == 'RJ'].groupby('data')['casosnovos'].sum().values

# 7. Média móvel de óbitos
mortes_dia = casos.groupby(['data']).agg({'mortesnovas': 'sum'}).reset_index().rename(columns={'mortesnovas': 'BR_mortes'})
mortes_dia['RJ_mortes'] = casos[casos['uf'] == 'RJ'].groupby('data')['mortesnovas'].sum().values
mortes_dia['mm_brasil'] = mortes_dia['BR_mortes'].rolling(window=7, min_periods=1).mean()
mortes_dia['mm_rj'] = mortes_dia['RJ_mortes'].rolling(window=7, min_periods=1).mean()

# 8. Acumulado RJ
rj = casos[casos['uf'] == 'RJ'].groupby('data').agg({'casosnovos': 'sum', 'mortesnovas': 'sum'}).reset_index()
rj['casosacumulado'] = rj['casosnovos'].cumsum()
rj['mortesacumulado'] = rj['mortesnovas'].cumsum()
rj_acumulado = rj

# 9. Tabela por Estado
tabela_estado = casos_estado.rename(columns={'uf': 'UF'})

# === MAPAS ===
shp_brasil = gpd.read_file("Mapas/BR_UF_2022.shp")
shp_brasil = shp_brasil.rename(columns={"CD_UF": "codigoibge"})
geojson_brasil = json.loads(shp_brasil.to_json())

mapa_brasil = px.choropleth(
    casos_estado.merge(shp_brasil, left_on="UF", right_on="SIGLA_UF"),
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

# === GRÁFICOS ===
bar_regiao = px.bar(casos_regiao, x="nomeregiao", y="taxa_casos_100k", title="Taxa de Casos por Região")
bar_sudeste = px.bar(casos_sudeste, x="uf", y="taxa_casos_100k", title="Taxa de Casos – Sudeste")
bar_top10_br = px.bar(top10_brasil, x="nomecidade", y="taxa_casos_100k", title="Top 10 Cidades – Brasil")
bar_top10_rj = px.bar(top10_rj, x="nomecidade", y="taxa_casos_100k", title="Top 10 Cidades – RJ")
linha_casos = px.line(casos_dia, x="data", y=["Brasil", "RJ"], title="Casos Novos por Dia")
linha_mortes = px.line(mortes_dia, x="data", y=["mm_brasil", "mm_rj"], title="Média Móvel de Mortes")
linha_rj = px.line(rj_acumulado, x="data", y=["casosacumulado", "mortesacumulado"], title="Casos e Mortes Acumuladas – RJ")

# === DASH APP ===
app = Dash(__name__)

app.layout = html.Div([
    html.H1("Painel Epidemiológico – G2"),

    html.Div([
        html.Div([
            html.H3("Mapa – Casos por Estado"),
            dcc.Graph(figure=mapa_brasil)
        ], style={'width': '49%', 'display': 'inline-block'}),
        html.Div([
            html.H3("Mapa – Casos por Município (RJ)"),
            dcc.Graph(figure=mapa_rj)
        ], style={'width': '49%', 'display': 'inline-block'}),
    ]),

    html.Div([
        dcc.Graph(figure=bar_regiao),
        dcc.Graph(figure=bar_sudeste),
    ], style={'columnCount': 2}),

    html.Div([
        dcc.Graph(figure=bar_top10_br),
        dcc.Graph(figure=bar_top10_rj),
    ], style={'columnCount': 2}),

    html.Div([
        dcc.Graph(figure=linha_casos),
        dcc.Graph(figure=linha_mortes)
    ], style={'columnCount': 2}),

    html.Div([
        dcc.Graph(figure=linha_rj)
    ]),

    html.Div([
        html.H3("Tabela por Estado"),
        dash_table.DataTable(
            data=tabela_estado.to_dict("records"),
            columns=[{"name": i, "id": i} for i in tabela_estado.columns],
            page_size=15,
            style_table={'overflowY': 'auto'},
            style_cell={"textAlign": "center"}
        )
    ])
])

if __name__ == "__main__":
    app.run(debug=True)
