# %%
import dash
from dash import dcc, html, dash_table
import plotly.express as px
import plotly.graph_objs as go
import pandas as pd
import geopandas as gpd
import json
import sqlite3

# ======= CONEXÃO E LEITURA DO BANCO ============
# Certifique-se de que o arquivo G2.db está na pasta 'Data' ou ajuste o caminho
conn = sqlite3.connect("Data/G2.db")

df_casos_municipais = pd.read_sql("SELECT * FROM CasosMunicipais", conn)
df_municipios = pd.read_sql("SELECT * FROM Municipio", conn)
df_estados = pd.read_sql("SELECT * FROM Estado", conn)
df_regioes = pd.read_sql("SELECT * FROM Regiao", conn)
conn.close()



# %%
# ======= PRÉ-PROCESSAMENTO ==========

# Juntar tabelas
df_casos_municipais["data"] = pd.to_datetime("1970-01-01") + pd.to_timedelta(df_casos_municipais["data"], unit="D")
df = df_casos_municipais.merge(df_municipios, on="codigomunicipal", suffixes=("", "_mun"))
df = df.merge(df_estados, on="codigoestadual", suffixes=("", "_est"))
df = df.merge(df_regioes, on="codigoregiao", suffixes=("", "_reg"))

# INDICADORES PRINCIPAIS (Brasil, RJ, Município do RJ)
total_casos_brasil = int(df["casosnovos"].sum())
total_obitos_brasil = int(df["mortesnovas"].sum())
# <> Corrigido para somar a população de cada estado uma única vez
pop_brasil = int(df["populacao_est"].unique().sum())

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

# %%
# ====== Top 10 cidades Brasil e RJ ======
df_cidade_brasil = df.groupby(["uf", "nomecidade"]).agg({
    "casosnovos": "sum",
    "mortesnovas": "sum",
    "populacao": "first"
}).reset_index()
df_cidade_brasil["Taxa"] = (100000 * df_cidade_brasil["casosnovos"] / df_cidade_brasil["populacao"]).fillna(0)
df_cidade_brasil["Letalidade"] = (100 * df_cidade_brasil["mortesnovas"] / df_cidade_brasil["casosnovos"]).fillna(0)
df_cidade_brasil["Mortalidade"] = (100000 * df_cidade_brasil["mortesnovas"] / df_cidade_brasil["populacao"]).fillna(0)
df_top_mun_brasil = df_cidade_brasil.sort_values("Taxa", ascending=False).head(10)
df_top_mun_brasil = df_top_mun_brasil.rename(columns={"uf": "UF", "nomecidade": "Nome"})
df_top_mun_brasil = df_top_mun_brasil[["UF", "Nome", "Taxa", "Letalidade", "Mortalidade"]]

df_cidade_rj = df_cidade_brasil[df_cidade_brasil["uf"] == "RJ"]
df_top_mun_rj = df_cidade_rj.sort_values("Taxa", ascending=False).head(10)
df_top_mun_rj = df_top_mun_rj.rename(columns={"uf": "UF", "nomecidade": "Nome"})
df_top_mun_rj = df_top_mun_rj[["Nome", "Taxa", "Letalidade", "Mortalidade"]]

# %%
# ====== Casos por Região e Sudeste ======
df_regiao = df.groupby("nomeregiao").agg({
    "casosnovos": "sum",
    "populacao_est": "sum"
}).reset_index()
df_regiao['Casos por 100 mil hab'] = (100_000 * df_regiao['casosnovos'] / df_regiao['populacao_est']).fillna(0)
df_regiao = df_regiao.rename(columns={"nomeregiao": "Região"})

df_sudeste = df[df["nomeregiao"] == "Sudeste"]
df_estado_sudeste = df_sudeste.groupby("uf").agg({
    "casosnovos": "sum",
    "populacao_est": "sum"
}).reset_index()
df_estado_sudeste['Casos por 100 mil hab'] = (100_000 * df_estado_sudeste['casosnovos'] / df_estado_sudeste['populacao_est']).fillna(0)
df_estado_sudeste = df_estado_sudeste.rename(columns={"uf": "Estado"})

# %%
# ====== Gráficos de Barra ======
fig_bar_regiao = px.bar(
    df_regiao, y="Região", x="Casos por 100 mil hab", orientation="h", color="Região",
    text=df_regiao["Casos por 100 mil hab"].map("{:.2f}".format),
    title="Casos a cada 100 mil habitantes por Região"
)
fig_bar_regiao.update_layout(showlegend=False, height=220, margin=dict(l=40, r=10, t=40, b=20))
fig_bar_regiao.update_traces(textposition='outside')

fig_bar_sudeste = px.bar(
    df_estado_sudeste, y="Estado", x="Casos por 100 mil hab", orientation="h", color="Estado",
    text=df_estado_sudeste["Casos por 100 mil hab"].map("{:.2f}".format),
    title="Casos a cada 100 mil habitantes por Estado do Sudeste"
)
fig_bar_sudeste.update_layout(showlegend=False, height=180, margin=dict(l=40, r=10, t=40, b=20))
fig_bar_sudeste.update_traces(textposition='outside')


# %%
# =====================================================================
# <> INÍCIO DA SEÇÃO DO MAPA DO BRASIL (REFEITA)
# =====================================================================
# 1. Carregue o shapefile do Brasil
# Carregar shapefile e preparar GeoJSON
shp_brasil = gpd.read_file("Mapas/BR_UF_2022.shp")
shp_brasil = shp_brasil.rename(columns={"CD_UF": "codigoibge"})
geojson_brasil = json.loads(shp_brasil.to_json())

# Verifique se df_estados_table tem a coluna 'UF' e se os dados batem com a coluna 'SIGLA_UF' do shapefile
df_casos_estado = df.groupby("uf").agg({
    "casosnovos": "sum",
    "mortesnovas": "sum",
    "populacao_est": "sum"
}).reset_index()

df_casos_estado["Letalidade"] = 100 * df_casos_estado["mortesnovas"] / df_casos_estado["casosnovos"]
df_casos_estado["Mortalidade por 100.000"] = 100000 * df_casos_estado["mortesnovas"] / df_casos_estado["populacao_est"]

df_estados_table = df_casos_estado.rename(columns={
    "uf": "UF",
    "casosnovos": "Confirmados",
    "mortesnovas": "Óbitos",
    "populacao_est": "População"
})

# === Merge com shapefile via UF e SIGLA_UF ===
df_plot_brasil = df_estados_table.merge(shp_brasil, left_on="UF", right_on="SIGLA_UF")

# === Mapa ===
mapa_brasil = px.choropleth(
    df_plot_brasil,
    geojson=geojson_brasil,
    locations="codigoibge",  # chave usada no GeoJSON
    color="Confirmados",
    featureidkey="properties.codigoibge",
    title="Casos Confirmados por Estado – Brasil"
)

mapa_brasil.update_geos(fitbounds="locations", visible=False)
mapa_brasil.update_layout(margin={"r":0,"t":30,"l":0,"b":0})
# # ====== Casos por Estado ======
# df_casos_estado_rj = df_rj.groupby("codigomunicipal").agg({
#     "casosnovos": "sum",
#     "mortesnovas": "sum",
#     "populacao_est": "sum"
# }).reset_index()
# df_casos_estado_rj = df_casos_estado_rj.rename(columns={
#     "casosnovos": "Total de Casos",
# })[["codigomunicipal","Total de Casos"]]
# df_casos_estado_rj
# shp_rj = gpd.read_file("Mapas/RJ_Municipios_2022.shp")
# shp_rj = shp_rj.rename(columns={"CD_MUN": "codigomunicipal"})
# geojson_rj = json.loads(shp_rj.to_json())

# # === Merge com shapefile via UF e SIGLA_UF ===
# df_plot_rj = df_casos_estado_rj.merge(shp_rj, left_on="uf", right_on="SIGLA_UF")

# mapa_rj = px.choropleth(
#     df_casos_estado_rj,
#     geojson=geojson_rj,
#     locations="codigomunicipal",
#     color="Total de Casos",
#     featureidkey="properties.codigomunicipal",
#     title="Casos Confirmados por Município – RJ"
# )

# mapa_rj.update_geos(fitbounds="locations", visible=False)
# # =====================================================================
# # <> FIM DA SEÇÃO DO MAPA DO BRASIL
# # =====================================================================


# %%
# =====================================================================
# <> INÍCIO DA SEÇÃO DO MAPA DO RJ (REFEITA)
# =====================================================================
# 1. Agregue os dados por município do RJ
df_casos_municipio_rj = df_rj.groupby("codigomunicipal").agg({
    "casosnovos": "sum"
}).reset_index()


# 2. Carregue o shapefile do RJ
# shp_rj = gpd.read_file("Mapas/RJ_Municipios_2022.shp")
# 2. Carregar shapefile
shp_rj = gpd.read_file("Mapas/RJ_Municipios_2022.shp")
shp_rj = shp_rj.rename(columns={"CD_MUN": "codigomunicipal"})

# 3. Garantir que as chaves sejam do mesmo tipo
df_casos_municipio_rj['codigomunicipal'] = df_casos_municipio_rj['codigomunicipal'].astype(int)
shp_rj['codigomunicipal'] = shp_rj['codigomunicipal'].astype(int)

# 4. Merge para juntar geometria e dados
map_data_rj = shp_rj.merge(df_casos_municipio_rj, on="codigomunicipal")

# 5. Criar geojson separado
geojson_rj = json.loads(map_data_rj.to_json())

# 6. Criar o mapa correto
mapa_rj = px.choropleth(
    map_data_rj,
    geojson=geojson_rj,
    locations="codigomunicipal",
    color="casosnovos",
    featureidkey="properties.codigomunicipal",
    hover_name="NM_MUN",
    title="Casos Confirmados por Município – RJ"
)

mapa_rj.update_geos(fitbounds="locations", visible=False)
mapa_rj.update_layout(margin={"r":0,"t":40,"l":0,"b":0})
# =====================================================================
# <> FIM DA SEÇÃO DO MAPA DO RJ
# =====================================================================


# %%
# ====== GRÁFICOS DE SÉRIES TEMPORAIS (sem alterações) ======
# Casos novos por dia Brasil e RJ
casos_brasil = df.groupby('data')['casosnovos'].sum().reset_index().rename(columns={'casosnovos':'Brasil'})
casos_rj = df[df['uf'] == 'RJ'].groupby('data')['casosnovos'].sum().reset_index().rename(columns={'casosnovos':'RJ'})
casos_dia = pd.merge(casos_brasil, casos_rj, on='data', how='outer').sort_values('data').fillna(0)
casos_dia_long = casos_dia.melt(id_vars='data', value_vars=['Brasil', 'RJ'], var_name='local', value_name='casos')

fig_casos_dia = px.line(
    casos_dia_long, x="data", y="casos", color="local", markers=True,
    labels={"data": "Dia", "casos": "Casos Novos"}
)
fig_casos_dia.update_layout(
    margin=dict(l=20, r=10, t=25, b=25), title="", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)

# Óbitos por dia e média móvel
obitos_brasil = df.groupby('data')['mortesnovas'].sum().reset_index().rename(columns={'mortesnovas':'Brasil'})
obitos_rj = df[df['uf'] == 'RJ'].groupby('data')['mortesnovas'].sum().reset_index().rename(columns={'mortesnovas':'RJ'})
obitos_dia = pd.merge(obitos_brasil, obitos_rj, on='data', how='outer').sort_values('data').fillna(0)
obitos_dia['mm_brasil'] = obitos_dia['Brasil'].rolling(window=7, min_periods=1).mean()
obitos_dia['mm_rj'] = obitos_dia['RJ'].rolling(window=7, min_periods=1).mean()
mmelt = obitos_dia.melt(id_vars='data', value_vars=['mm_brasil', 'mm_rj'], var_name='local', value_name='media_movel')
mmelt['local'] = mmelt['local'].replace({'mm_brasil': 'Brasil', 'mm_rj': 'RJ'})

fig_media_obitos = px.line(
    mmelt, x='data', y='media_movel', color='local', markers=True,
    labels={"data": "Dia", "media_movel": "Média Móvel de Óbitos"}
)
fig_media_obitos.update_layout(
    margin=dict(l=20, r=10, t=25, b=25), title="", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)

# Acumulados RJ
rj_acumulado = df_rj.groupby('data').agg({'casosnovos': 'sum', 'mortesnovas': 'sum'}).reset_index().sort_values('data')
rj_acumulado['casosacumulado'] = rj_acumulado['casosnovos'].cumsum()
rj_acumulado['mortesacumulado'] = rj_acumulado['mortesnovas'].cumsum()

fig_acumulados_rj = go.Figure()
fig_acumulados_rj.add_trace(go.Scatter(x=rj_acumulado['data'], y=rj_acumulado['casosacumulado'], mode='lines+markers', name="Casos", line=dict(color="blue")))
fig_acumulados_rj.add_trace(go.Scatter(x=rj_acumulado['data'], y=rj_acumulado['mortesacumulado'], mode='lines+markers', name="Óbitos", line=dict(color="red")))
fig_acumulados_rj.update_layout(
    margin=dict(l=20, r=10, t=25, b=25), title="", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    xaxis_title="Data", yaxis_title="Acumulado"
)


# %%
# ========== DASH APP LAYOUT (sem alterações) ==========
caixa_kpi_style = {"border": "2px solid #0074D9", "borderRadius": "20px", "padding": "6px 8px", "margin": "2px", "background": "#fff", "boxSizing": "border-box", "minHeight": "80px", "flex": "1 1 0", "whiteSpace": "normal", "overflow": "hidden", "display": "flex", "flexDirection": "column", "justifyContent": "center"}
altura_mapa = "250px" # <> Aumentei um pouco a altura para melhor visualização
altura_grafico = "220px"
altura_tabela = "220px"
caixa_coluna_style = {"border": "2px solid #0074D9", "borderRadius": "20px", "padding": "10px", "margin": "2px", "background": "#fff", "boxSizing": "border-box", "display": "flex", "flexDirection": "column", "justifyContent": "flex-start", "flex": "1", 'margin': '0 5px'}
kpi_title = {"marginBottom": "1px", "fontSize": "15px"}
kpi_li_style = {"marginLeft": "6px", "fontSize": "13px", "lineHeight": "1.1"}
caixa_style_grafico = {"border": "2px solid #0074D9", "borderRadius": "20px", "padding": "10px", "background": "#fff", "boxSizing": "border-box"}

app = dash.Dash(__name__, suppress_callback_exceptions=True)
app.title = "INF1514_G2_2_Python_Painel"
app.layout = html.Div([
    html.H2("Painel COVID-19: Análise de Dados", style={"textAlign": "center", "marginTop": "10px", "color": "#0074D9"}),
    dcc.Tabs(id="tabs-gerais", children=[
        dcc.Tab(label="Painel Geral", children=[
            # KPIs TOP
            html.Div([
                html.Div([html.B("Total de casos confirmados"), html.Ul([html.Li(["Brasil", html.Br(), html.Span(indicadores['casos_brasil'], style={"color":"#0074D9", "fontWeight":"bold"})], style=kpi_li_style), html.Li(["Estado do Rio de Janeiro", html.Br(), html.Span(indicadores['casos_rj'], style={"color":"#0074D9", "fontWeight":"bold"})], style=kpi_li_style), html.Li(["Cidade do Rio de Janeiro", html.Br(), html.Span(indicadores['casos_mun_rj'], style={"color":"#0074D9", "fontWeight":"bold"})], style=kpi_li_style),])], style=caixa_kpi_style),
                html.Div([html.B("Total de óbitos"), html.Ul([html.Li(["Brasil", html.Br(), html.Span(indicadores['obitos_brasil'], style={"color":"#ff9900", "fontWeight":"bold"})], style=kpi_li_style), html.Li(["Estado do Rio de Janeiro", html.Br(), html.Span(indicadores['obitos_rj'], style={"color":"#ff9900", "fontWeight":"bold"})], style=kpi_li_style), html.Li(["Cidade do Rio de Janeiro", html.Br(), html.Span(indicadores['obitos_mun_rj'], style={"color":"#ff9900", "fontWeight":"bold"})], style=kpi_li_style),])], style=caixa_kpi_style),
                html.Div([html.B("Letalidade ", style=kpi_title), html.Span("(total de óbitos / total de casos)", style={"fontSize":"11px"}), html.Ul([html.Li(["Brasil", html.Br(), html.Span(indicadores['letalidade_brasil'], style={"color":"#9933ff", "fontWeight":"bold"})], style=kpi_li_style), html.Li(["Estado do Rio de Janeiro", html.Br(), html.Span(indicadores['letalidade_rj'], style={"color":"#9933ff", "fontWeight":"bold"})], style=kpi_li_style), html.Li(["Cidade do Rio de Janeiro", html.Br(), html.Span(indicadores['letalidade_mun_rj'], style={"color":"#9933ff", "fontWeight":"bold"})], style=kpi_li_style),])], style=caixa_kpi_style),
                html.Div([html.B("Mortalidade ", style=kpi_title), html.Span("(total de óbitos / população)", style={"fontSize":"11px"}), html.Ul([html.Li(["Brasil", html.Br(), html.Span(indicadores['mortalidade_brasil'], style={"color":"#e60000", "fontWeight":"bold"})], style=kpi_li_style), html.Li(["Estado do Rio de Janeiro", html.Br(), html.Span(indicadores['mortalidade_rj'], style={"color":"#e60000", "fontWeight":"bold"})], style=kpi_li_style), html.Li(["Cidade do Rio de Janeiro", html.Br(), html.Span(indicadores['mortalidade_mun_rj'], style={"color":"#e60000", "fontWeight":"bold"})], style=kpi_li_style),])], style=caixa_kpi_style),
            ], style={"display": "flex", "width":"100%", "marginBottom":"8px"}),

            # Linha principal com mapas, gráficos e tabelas
            html.Div([
                # COLUNA 1: Mapas
                html.Div([
                    html.B("Distribuição de Casos", style={'textAlign': 'center', 'display': 'block'}),
                    dcc.Graph(figure=mapa_brasil, config={"displayModeBar": False}, style={"height": altura_mapa}),
                    dcc.Graph(figure=mapa_rj, config={"displayModeBar": False}, style={"height": altura_mapa, "marginTop": "10px"}),
                ], style=caixa_coluna_style),
                # COLUNA 2: Gráficos de barras e Tabelas
                html.Div([
                    html.B("Casos por Região e Cidades", style={'textAlign': 'center', 'display': 'block'}),
                    dcc.Graph(figure=fig_bar_regiao, config={"displayModeBar": False}, style={"height": altura_grafico}),
                    dcc.Graph(figure=fig_bar_sudeste, config={"displayModeBar": False}, style={"height": altura_grafico}),
                ], style=caixa_coluna_style),
                # COLUNA 3: Tabelas top 10
                html.Div([
                    html.B("Top 10 Cidades (Taxa/100k hab.)", style={'textAlign': 'center', 'display': 'block'}),
                    html.H6("Brasil", style={"textAlign":"center", "marginTop":"5px", "marginBottom":"5px"}),
                    dash_table.DataTable(data=df_top_mun_brasil.to_dict("records"), columns=[{"name": i, "id": i} for i in df_top_mun_brasil.columns], style_table={"height": altura_tabela, "overflowY": "auto"}, style_cell={"textAlign": "center"}, page_size=10),
                    html.H6("Estado do RJ", style={"textAlign":"center", "marginTop":"10px", "marginBottom":"5px"}),
                    dash_table.DataTable(data=df_top_mun_rj.to_dict("records"), columns=[{"name": i, "id": i} for i in df_top_mun_rj.columns], style_table={"height": altura_tabela, "overflowY": "auto"}, style_cell={"textAlign": "center"}, page_size=10),
                ], style=caixa_coluna_style),
            ], style={"width": "100%", "display": "flex", "justifyContent": "space-between", "marginBottom": "8px"}),
        ]),

        # PAINEL DE CASOS DIÁRIOS
        dcc.Tab(label="Análise Temporal e por Estado", children=[
            html.Div([
                # Coluna de Gráficos Temporais
                html.Div([
                    html.Div([html.B("Casos novos por dia"), dcc.Graph(figure=fig_casos_dia, config={"displayModeBar": False}, style={"height": "250px"})], style={**caixa_style_grafico, 'marginBottom':'10px'}),
                    html.Div([html.B("Média móvel de óbitos (7 dias)"), dcc.Graph(figure=fig_media_obitos, config={"displayModeBar": False}, style={"height": "250px"})], style={**caixa_style_grafico, 'marginBottom':'10px'}),
                    html.Div([html.B("Casos e óbitos acumulados no RJ"), dcc.Graph(figure=fig_acumulados_rj, config={"displayModeBar": False}, style={"height": "250px"})], style=caixa_style_grafico),
                ], style={"width": "54%", "marginRight": "1%"}),
                # Coluna da Tabela de Estados
                html.Div([
                    html.B("Dados Consolidados por Estado"),
                    dash_table.DataTable(
                        data=df_estados_table.to_dict("records"),
                        columns=[{"name": i, "id": i} for i in df_estados_table.columns],
                        style_table={"height": "800px", "overflowY": "auto"},
                        style_cell={"textAlign": "center"},
                        page_size=27,
                        sort_action="native",
                        filter_action="native"
                    ),
                ], style={**caixa_style_grafico, "width": "45%"}),
            ], style={"width": "100%", "display": "flex", "flexDirection": "row", "alignItems": "flex-start", "justifyContent": "space-between", "marginTop": "10px"}),
        ]),
    ]),
], style={"background": "#f0f0f0", "padding": "10px"})

if __name__ == "__main__":
    app.run(debug=True)