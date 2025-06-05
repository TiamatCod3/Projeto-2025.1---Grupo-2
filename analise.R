# 📦 Carregamento de pacotes
# install.packages("readr")
# install.packages("dplyr")
# install.packages("RSQLite")
# install.packages("shiny")
# install.packages("shinydashboard")
# install.packages("zoo")  
# install.packages("sf")
# install.packages("DT")


library(readr)
library(dplyr)
library(DBI)
library(RSQLite)
library(ggplot2)
library(shiny)
library(shinydashboard)
library(zoo)
library(sf)
library(DT)



# ETAPA 1 - LEITURA DOS DADOS
casos <- read_delim(
  "Data/Casos.csv",
  delim = ";",
  col_types = cols(
    codigoibge = col_character()
  ),
  show_col_types = FALSE
)

# Conexão com Base.db
base_conn <- dbConnect(SQLite(), "Data/Base.db")
regioes <- dbReadTable(base_conn, "Regiao")
estados <- dbReadTable(base_conn, "Estado")
dbDisconnect(base_conn)

# ETAPA 2: TRATAMENTO E LIMPEZA DOS DADOS
casos_padronizados <- casos %>%
  mutate(
    data = as.Date(data, format = "%d/%m/%Y"),
    casosnovos = ifelse(is.na(casosnovos), 0, casosnovos),
    mortesnovas = ifelse(is.na(mortesnovas), 0, mortesnovas)
  ) %>%
  mutate(idcaso = row_number()) %>%
  select(idcaso, tipo, codigoibge, nomelocalidade, uf, populacao, data, casosnovos, mortesnovas)

# Normalização das tabelas auxiliares
names(estados) <- tolower(names(estados))
names(regioes) <- tolower(names(regioes))
estados <- estados %>% rename(codigoestadual = codigoibge)

# MUNICÍPIOS
municipios <- casos_padronizados %>%
  filter(tipo == "city") %>%
  distinct(codigoibge, nomelocalidade, uf, populacao) %>%
  rename(codigomunicipal = codigoibge, nomecidade = nomelocalidade, codigoestado_uf = uf)

municipios_joined <- municipios %>%
  left_join(estados %>% select(codigoestadual, uf), by = c("codigoestado_uf" = "uf")) %>%
  select(codigomunicipal, nomecidade, codigoestadual, populacao)

municipios_filtrados <- municipios_joined %>%
  filter(!is.na(codigomunicipal), !is.na(nomecidade), !is.na(codigoestadual), !is.na(populacao)) %>%
  mutate(codigomunicipal = as.character(codigomunicipal), codigoestadual = as.character(codigoestadual))

# CARGA MUNICÍPIOS
conn <- dbConnect(SQLite(), "Data/G2.db")
dbExecute(conn, "DROP TABLE IF EXISTS Municipio")
dbExecute(conn, "
CREATE TABLE Municipio (
  codigomunicipal TEXT PRIMARY KEY,
  nomecidade TEXT,
  codigoestadual TEXT,
  populacao INTEGER,
  FOREIGN KEY (codigoestadual) REFERENCES Estado(codigoestadual)
);")
dbWriteTable(conn, "Municipio", municipios_filtrados, append = TRUE, row.names = FALSE)
dbDisconnect(conn)

# ESTADOS E REGIÕES
populacao_estado <- municipios_filtrados %>%
  group_by(codigoestadual) %>% summarise(populacao = sum(populacao)) %>%
  mutate(codigoestadual = as.character(codigoestadual))

estados <- estados %>% mutate(codigoestadual = as.character(codigoestadual))

estados_final <- estados %>%
  left_join(populacao_estado, by = "codigoestadual") %>%
  select(codigoestadual, nomeestado, uf, codigoregiao, populacao)

conn <- dbConnect(SQLite(), "Data/G2.db")
dbExecute(conn, "DROP TABLE IF EXISTS Estado")
dbExecute(conn, "
CREATE TABLE Estado (
  codigoestadual TEXT PRIMARY KEY,
  nomeestado TEXT,
  uf TEXT,
  codigoregiao INTEGER,
  populacao INTEGER,
  FOREIGN KEY (codigoregiao) REFERENCES Regiao(codigoregiao)
);")
dbWriteTable(conn, "Estado", estados_final, append = TRUE, row.names = FALSE)
dbDisconnect(conn)

populacao_regiao <- estados_final %>% group_by(codigoregiao) %>% summarise(populacao = sum(populacao))
regioes_final <- regioes %>% left_join(populacao_regiao, by = "codigoregiao") %>% select(codigoregiao, nomeregiao, populacao)

conn <- dbConnect(SQLite(), "Data/G2.db")
dbExecute(conn, "DROP TABLE IF EXISTS Regiao")
dbExecute(conn, "
CREATE TABLE Regiao (
  codigoregiao INTEGER PRIMARY KEY,
  nomeregiao TEXT,
  populacao INTEGER
);")
dbWriteTable(conn, "Regiao", regioes_final, append = TRUE, row.names = FALSE)
dbDisconnect(conn)

# CASOS DESCARTADOS
casos_descartados <- casos_padronizados %>%
  filter(
    is.na(codigoibge) | codigoibge == "" |
      (tipo == "city" & !(codigoibge %in% municipios_filtrados$codigomunicipal)) |
      (tipo == "state" & !(codigoibge %in% estados_final$codigoestadual)) |
      (tipo == "city" & nchar(codigoibge) <= 2) |
      (tipo == "state" & nchar(codigoibge) >= 7) |
      (casosnovos == 0 & mortesnovas == 0)
  )
write_delim(casos_descartados, "Data/Descartados.csv", delim = ";")
ids_descartados <- casos_descartados$idcaso

casos_padronizados_validos <- casos_padronizados %>%
  filter(!(idcaso %in% ids_descartados)) %>%
  mutate(codigoibge = as.character(codigoibge), nomelocalidade = as.character(nomelocalidade), uf = as.character(uf))

# CARGA CASOS PADRONIZADOS
conn <- dbConnect(SQLite(), "Data/G2.db")
dbExecute(conn, "DROP TABLE IF EXISTS CasosPadronizados")
dbExecute(conn, "
CREATE TABLE CasosPadronizados (
  idcaso INTEGER PRIMARY KEY,
  tipo TEXT,
  codigoibge TEXT,
  nomelocalidade TEXT,
  uf TEXT,
  populacao INTEGER,
  data DATE,
  casosnovos INTEGER,
  mortesnovas INTEGER
);")
dbWriteTable(conn, "CasosPadronizados", casos_padronizados_validos, append = TRUE, row.names = FALSE)
dbDisconnect(conn)

# CASOS MUNICIPAIS E ESTADUAIS
casos_municipais_validos <- casos_padronizados_validos %>%
  filter(tipo == "city") %>%
  transmute(
    idcaso,
    codigomunicipal = codigoibge,
    data = as.Date(data),
    casosnovos,
    mortesnovas
  )

casos_estaduais_validos <- casos_padronizados_validos %>%
  filter(tipo == "state") %>%
  transmute(
    idcaso,
    codigoestadual = codigoibge,
    data = as.Date(data),
    casosnovos,
    mortesnovas
  )

conn <- dbConnect(SQLite(), "Data/G2.db")
dbExecute(conn, "DROP TABLE IF EXISTS CasosMunicipais")
dbExecute(conn, "DROP TABLE IF EXISTS CasosEstaduais")

dbExecute(conn, "
CREATE TABLE CasosMunicipais (
  idcaso INTEGER,
  codigomunicipal TEXT,
  data DATE,
  casosnovos INTEGER,
  mortesnovas INTEGER,
  FOREIGN KEY (codigomunicipal) REFERENCES Municipio(codigomunicipal)
);")

dbExecute(conn, "
CREATE TABLE CasosEstaduais (
  idcaso INTEGER,
  codigoestadual TEXT,
  data DATE,
  casosnovos INTEGER,
  mortesnovas INTEGER,
  FOREIGN KEY (codigoestadual) REFERENCES Estado(codigoestadual)
);")

dbWriteTable(conn, "CasosMunicipais", casos_municipais_validos, append = TRUE, row.names = FALSE)
dbWriteTable(conn, "CasosEstaduais", casos_estaduais_validos, append = TRUE, row.names = FALSE)
dbDisconnect(conn)

#=========================== CARGA E TRATAMENTO FINALIZADO ============================================

# 📂 Conectar ao banco de dados G2.db
conn <- dbConnect(SQLite(), "Data/G2.db")

# 🧮 Query 1: Total de casos reportados pelos municípios (agregados por estado)
query_municipios <- "
SELECT e.nomeestado, m.codigoestadual, SUM(cm.casosnovos) AS casos_municipais
FROM CasosMunicipais cm
JOIN Municipio m ON m.codigomunicipal = cm.codigomunicipal
JOIN Estado e ON e.codigoestadual = m.codigoestadual
GROUP BY m.codigoestadual;
"

# 🧮 Query 2: Total de casos reportados diretamente pelos estados
query_estados <- "
SELECT e.nomeestado, e.codigoestadual, SUM(ce.casosnovos) AS casos_estaduais
FROM CasosEstaduais ce
JOIN Estado e ON e.codigoestadual = ce.codigoestadual
GROUP BY e.codigoestadual;
"

# 📤 Executar as queries
df_municipios <- dbGetQuery(conn, query_municipios)
df_estados <- dbGetQuery(conn, query_estados)

# 🔌 Fechar conexão com banco
dbDisconnect(conn)

# 🔀 Mesclar os dois dataframes
df_comparativo <- merge(df_municipios, df_estados,
                        by = c("codigoestadual", "nomeestado"),
                        all = TRUE)

# 📊 Calcular diferença absoluta e percentual
df_comparativo <- df_comparativo %>%
  mutate(
    diferenca = casos_municipais - casos_estaduais,
    percentual = round(100 * diferenca / casos_estaduais, 2)
  ) %>%
  arrange(nomeestado)

# 📈 Plotar gráfico de comparação
ggplot(df_comparativo, aes(x = reorder(nomeestado, -casos_municipais))) +
  geom_bar(aes(y = casos_municipais, fill = "Municípios"), stat = "identity", width = 0.4) +
  geom_bar(aes(y = casos_estaduais, fill = "Estados"), stat = "identity", width = 0.4, position = position_nudge(x = 0.4)) +
  labs(
    title = "Comparação de Casos Novos por Estado: Municípios vs Estados",
    x = "Estado",
    y = "Total de Casos Novos",
    fill = "Origem dos Dados"
  ) +
  theme_minimal() +
  theme(axis.text.x = element_text(angle = 90, hjust = 1))

# 💾 Exibir a tabela para auditoria
print(df_comparativo)

#=========================== DASHBOARD SHINY ======================
# 🔌 Conectar ao banco
conn <- dbConnect(SQLite(), "Data/G2.db")

# 📥 Carregar tabelas
casos_municipais <- dbReadTable(conn, "CasosMunicipais")
municipios <- dbReadTable(conn, "Municipio")
estados <- dbReadTable(conn, "Estado")
regioes <- dbReadTable(conn, "Regiao")


dbDisconnect(conn)

#=============== CALCULANDO OS PARÂMETROS ===========================
# 🔗 Join para relacionar município -> estado
casos_completos <- casos_municipais %>%
  left_join(municipios, by = "codigomunicipal") %>%
  left_join(estados, by = "codigoestadual") %>%
  left_join(regioes, by = "codigoregiao")

# ✅ Converter para tipo Date
casos_completos$data <- as.Date(casos_completos$data)

# 🇧🇷 Brasil
casos_brasil <- sum(casos_completos$casosnovos, na.rm = TRUE)
obitos_brasil <- sum(casos_completos$mortesnovas, na.rm = TRUE)
pop_brasil <- sum(estados$populacao, na.rm = TRUE)
letalidade_brasil <- round((obitos_brasil / casos_brasil) * 100, 2)
mortalidade_brasil <- round((obitos_brasil / pop_brasil) * 100000, 2)

# 🟦 Estado RJ
casos_rj <- casos_completos %>% filter(uf == "RJ")
casos_rj_total <- sum(casos_rj$casosnovos, na.rm = TRUE)
obitos_rj_total <- sum(casos_rj$mortesnovas, na.rm = TRUE)
pop_rj <- estados %>% filter(uf == "RJ") %>% pull(populacao)
letalidade_rj <- round((obitos_rj_total / casos_rj_total) * 100, 2)
mortalidade_rj <- round((obitos_rj_total / pop_rj) * 100000, 2)

# 🏙️ Município RJ
casos_mun_rj <- casos_completos %>% filter(codigomunicipal == "3304557")
casos_mun_rj_total <- sum(casos_mun_rj$casosnovos, na.rm = TRUE)
obitos_mun_rj_total <- sum(casos_mun_rj$mortesnovas, na.rm = TRUE)
pop_mun_rj <- municipios %>% filter(codigomunicipal == "3304557") %>% pull(populacao)
letalidade_mun_rj <- round((obitos_mun_rj_total / casos_mun_rj_total) * 100, 2)
mortalidade_mun_rj <- round((obitos_mun_rj_total / pop_mun_rj) * 100000, 2)



# 🎯 Agregar
top_municipios <- casos_completos %>%
  group_by(codigomunicipal, nomecidade, uf, populacao.x) %>%
  summarise(
    casos_total = sum(casosnovos, na.rm = TRUE),
    obitos_total = sum(mortesnovas, na.rm = TRUE),
    .groups = "drop"
  ) %>%
  mutate(
    taxa = casos_total / populacao.x,
    letalidade = obitos_total / casos_total,
    mortalidade = obitos_total / populacao.x
  ) %>%
  arrange(desc(taxa)) %>%
  slice_head(n = 10) %>%
  select(UF = uf, Nome = nomecidade, Taxa = taxa, Letalidade = letalidade, Mortalidade = mortalidade)

# 📊 Visualizar
print(top_municipios)

# 🎯 Filtrar apenas cidades do Estado do RJ
top_rj <- casos_completos %>%
  filter(uf == "RJ") %>%
  group_by(codigomunicipal, nomecidade, populacao.x) %>%
  summarise(
    casos_total = sum(casosnovos, na.rm = TRUE),
    obitos_total = sum(mortesnovas, na.rm = TRUE),
    .groups = "drop"
  ) %>%
  mutate(
    Taxa = casos_total / populacao.x,
    Letalidade = obitos_total / casos_total,
    Mortalidade = obitos_total / populacao.x
  ) %>%
  arrange(desc(Taxa)) %>%
  slice_head(n = 10) %>%
  select(Nome = nomecidade, Taxa, Letalidade, Mortalidade)

# 👁️ Visualizar resultado
print(top_rj)

casos_regiao <- casos_completos %>%
  group_by(codigoregiao, nomeregiao) %>%
  summarise(
    casos_total = sum(casosnovos, na.rm = TRUE),
    .groups = "drop"
  )

# 📊 Adicionar população da tabela Regiao
casos_regiao <- casos_regiao %>%
  left_join(regioes %>% select(codigoregiao, populacao), by = "codigoregiao") %>%
  mutate(taxa_incidencia = casos_total * 100 / populacao)



# 📈 Gráfico de barras
ggplot(casos_regiao, aes(x = reorder(nomeregiao, -taxa_incidencia), y = taxa_incidencia, fill = nomeregiao)) +
  geom_bar(stat = "identity", width = 0.7) +
  geom_text(aes(label = round(taxa_incidencia, 4)), vjust = -0.5, size = 5) +
  labs(
    title = "Taxa de Casos Confirmados por Região do Brasil (%)",
    x = "Região",
    y = "Taxa de Incidência (casos / habitante)",
    fill = "Região"
  ) +
  theme_minimal()


# 🎯 Agregar por UF
tabela_estados <- casos_completos %>%
  group_by(uf) %>%
  summarise(
    Confirmado = sum(casosnovos, na.rm = TRUE),
    Óbitos = sum(mortesnovas, na.rm = TRUE),
    Populacao = sum(populacao, na.rm = TRUE),
    .groups = "drop"
  ) %>%
  mutate(
    Letalidade = round(Óbitos / Confirmado, 4),
    Mortalidade = round(Óbitos / Populacao, 4)
  ) %>%
  arrange(uf) %>%
  select(UF = uf, Confirmado, Óbitos, Letalidade, Mortalidade)

# 👁️ Visualizar resultado
print(tabela_estados)




#========================== CASOS POR DIA
# 🟦 Total de casos por dia no Brasil
casos_brasil <- casos_completos %>%
  group_by(data) %>%
  summarise(casosnovos = sum(casosnovos, na.rm = TRUE), .groups = "drop") %>%
  mutate(entidade = "Brasil")

# 🟦 Total de casos por dia no RJ
casos_rj <- casos_completos %>%
  filter(uf == "RJ") %>%
  group_by(data) %>%
  summarise(casosnovos = sum(casosnovos, na.rm = TRUE), .groups = "drop") %>%
  mutate(entidade = "RJ")

# 🔄 Combinar e garantir dias ausentes com valor zero
datas_completas <- seq(min(casos_completos$data), max(casos_completos$data), by = "1 day")

df_brasil <- data.frame(data = datas_completas) %>%
  left_join(casos_brasil, by = "data") %>%
  mutate(
    casosnovos = ifelse(is.na(casosnovos), 0, casosnovos),
    entidade = "Brasil"
  )

df_rj <- data.frame(data = datas_completas) %>%
  left_join(casos_rj, by = "data") %>%
  mutate(
    casosnovos = ifelse(is.na(casosnovos), 0, casosnovos),
    entidade = "RJ"
  )

# 🧩 Combinar tudo
df_final <- bind_rows(df_brasil, df_rj) %>%
  arrange(data) %>%
  mutate(dia = row_number())

# 📊 Gráfico
ggplot(df_final, aes(x = dia, y = casosnovos, color = entidade)) +
  geom_point(size = 1.5) +
  geom_line() +
  labs(
    title = "Casos Novos por Dia – Brasil vs RJ",
    x = "Dia (contagem sequencial)",
    y = "Casos Novos",
    color = "Local"
  ) +
  theme_minimal()

#========================= MEDIA MOVEL DE OBITOS
# 🔷 Óbitos por dia - BR
obitos_brasil <- casos_completos %>%
  group_by(data) %>%
  summarise(obitos = sum(mortesnovas, na.rm = TRUE), .groups = "drop") %>%
  mutate(entidade = "Brasil")

# 🔷 Óbitos por dia - RJ
obitos_rj <- casos_completos %>%
  filter(uf == "RJ") %>%
  group_by(data) %>%
  summarise(obitos = sum(mortesnovas, na.rm = TRUE), .groups = "drop") %>%
  mutate(entidade = "RJ")

# ⛑️ Preencher com zero onde não há dados
df_brasil <- data.frame(data = datas_completas) %>%
  left_join(obitos_brasil, by = "data") %>%
  mutate(
    obitos = ifelse(is.na(obitos), 0, obitos),
    entidade = "Brasil"
  )

df_rj <- data.frame(data = datas_completas) %>%
  left_join(obitos_rj, by = "data") %>%
  mutate(
    obitos = ifelse(is.na(obitos), 0, obitos),
    entidade = "RJ"
  )

# 📈 Combinar e calcular média móvel
df_final <- bind_rows(df_brasil, df_rj) %>%
  arrange(data) %>%
  group_by(entidade) %>%
  mutate(
    media_movel = rollmean(obitos, k = 6, align = "right", fill = 0),
    dia = row_number()
  ) %>%
  ungroup()

# 🔍 Análise de tendência
tendencias <- df_final %>%
  group_by(entidade) %>%
  summarise(
    ultimo = last(media_movel),
    anterior = dplyr::nth(media_movel, n = n() - 14),
    variacao = round(100 * (ultimo - anterior) / ifelse(anterior == 0, 1, anterior), 1),
    tendencia = case_when(
      abs(variacao) <= 15 ~ "Estável",
      variacao > 15 ~ "Em crescimento",
      variacao < -15 ~ "Em queda",
      TRUE ~ "Indefinido"
    )
  )

print(tendencias)

# 🎯 Gráfico
ggplot(df_final, aes(x = dia, y = media_movel, color = entidade)) +
  geom_point(size = 1.3) +
  geom_line(size = 1) +
  labs(
    title = "Média Móvel de Óbitos – Brasil vs RJ (Janela: 6 dias)",
    subtitle = "Análise de tendência: variação entre o último dia e o 14º dia anterior",
    x = "Dia (contagem sequencial)",
    y = "Média Móvel de Óbitos",
    color = "Local"
  ) +
  theme_minimal()


#======================== CASOS ACUMULADOS POR DIA
# 🔴 Casos e óbitos por dia - Estado do RJ
dados_rj <- casos_completos %>%
  filter(uf == "RJ") %>%
  group_by(data) %>%
  summarise(
    casosnovos = sum(casosnovos, na.rm = TRUE),
    mortesnovas = sum(mortesnovas, na.rm = TRUE),
    .groups = "drop"
  )

# ⛑️ Preencher dias ausentes com zero
dados_rj_completo <- data.frame(data = datas_completas) %>%
  left_join(dados_rj, by = "data") %>%
  mutate(
    casosnovos = ifelse(is.na(casosnovos), 0, casosnovos),
    mortesnovas = ifelse(is.na(mortesnovas), 0, mortesnovas)
  ) %>%
  mutate(
    casos_acumulados = cumsum(casosnovos),
    obitos_acumulados = cumsum(mortesnovas),
    dia = row_number()
  )

# 📊 Gráfico
ggplot(dados_rj_completo) +
  geom_point(aes(x = dia, y = casos_acumulados), color = "blue", size = 1.5) +
  geom_line(aes(x = dia, y = casos_acumulados), color = "blue", linewidth = 1) +
  geom_point(aes(x = dia, y = obitos_acumulados), color = "red", size = 1.5) +
  geom_line(aes(x = dia, y = obitos_acumulados), color = "red", linewidth = 1) +
  labs(
    title = "Casos e Óbitos Acumulados – Estado do Rio de Janeiro",
    x = "Dia (contagem sequencial)",
    y = "Total acumulado"
  ) +
  theme_minimal()


#=================== MAPA DE CASOS NO BRASIL
casos_estado <- casos_completos %>%
  group_by(uf) %>%
  summarise(casos_total = sum(casosnovos, na.rm = TRUE), .groups = "drop")

shape_brasil <- st_read("Mapas/BR_UF_2022.shp", quiet = TRUE)

# 🔗 Juntar com dados de casos
shape_brasil_dados <- shape_brasil %>%
  left_join(casos_estado, by = c("SIGLA_UF" = "uf"))  # ajuste conforme o nome da coluna

# 🗺️ Gráfico
ggplot(shape_brasil_dados) +
  geom_sf(aes(fill = casos_total), color = "white", size = 0.2) +
  scale_fill_gradient(low = "#deebf7", high = "#08519c", na.value = "grey90") +
  labs(
    title = "Casos Confirmados Acumulados por Estado – Brasil",
    fill = "Casos"
  ) +
  theme_minimal()



#============ MUNICIPIOS DO RJ

# ✅ Agregar casos acumulados por município
casos_municipio_rj <- casos_completos %>%
  filter(codigoestadual == "33") %>%  # RJ = 33
  group_by(codigomunicipal) %>%
  summarise(casos_total = sum(casosnovos, na.rm = TRUE), .groups = "drop")

# 🌍 Ler shapefile do RJ por municípios
mapa_rj <- st_read("Mapas/RJ_Municipios_2022.shp", quiet = TRUE)

# Ajuste "CD_MUN" conforme o nome da coluna do código IBGE no shapefile
mapa_rj_dados <- mapa_rj %>%
  mutate(codigomunicipal = as.character(CD_MUN)) %>%
  left_join(casos_municipio_rj, by = "codigomunicipal")

# 🗺️ Gráfico
ggplot(mapa_rj_dados) +
  geom_sf(aes(fill = casos_total), color = "white", linewidth = 0.2) +
  scale_fill_gradient(low = "#fee0d2", high = "#de2d26", na.value = "grey90") +
  labs(
    title = "Casos Confirmados Acumulados por Município – Estado do RJ",
    fill = "Casos acumulados"
  ) +
  theme_minimal()

names(mapa_rj)


#=========================== SHINY SERVER
ui <- dashboardPage(
  dashboardHeader(title = "Painel COVID-19 - RJ"),
  dashboardSidebar(
    sidebarMenu(
      menuItem("Resumo", tabName = "resumo", icon = icon("dashboard")),
      menuItem("Tabelas", tabName = "tabelas", icon = icon("table")),
      menuItem("Gráficos", tabName = "graficos", icon = icon("chart-line")),
      menuItem("Mapas", tabName = "mapas", icon = icon("globe"))
    )
  ),
  dashboardBody(
    tabItems(
      # Aba Resumo
      tabItem(tabName = "resumo",
              fluidRow(
                valueBoxOutput("casos_brasil"),
                valueBoxOutput("casos_rj"),
                valueBoxOutput("casos_mun_rj")
              ),
              fluidRow(
                valueBoxOutput("letalidade_brasil"),
                valueBoxOutput("letalidade_rj"),
                valueBoxOutput("letalidade_mun_rj")
              )
      ),
      
      # Aba Tabelas
      tabItem(tabName = "tabelas",
              fluidRow(
                box(title = "Top 10 Cidades com Maior Taxa de Casos", width = 12, DT::dataTableOutput("top_municipios"))
              ),
              fluidRow(
                box(title = "Top 10 Cidades do RJ", width = 12, DT::dataTableOutput("top_rj"))
              ),
              fluidRow(
                box(title = "Resumo por Estado", width = 12, DT::dataTableOutput("tabela_estados"))
              )
      ),
      
      # Aba Gráficos
      tabItem(tabName = "graficos",
              fluidRow(
                box(title = "Casos por Dia", width = 12, plotOutput("grafico_casos_dia"))
              ),
              fluidRow(
                box(title = "Média Móvel de Óbitos", width = 12, plotOutput("grafico_media_obitos"))
              ),
              fluidRow(
                box(title = "Casos e Óbitos Acumulados RJ", width = 12, plotOutput("grafico_acumulados_rj"))
              )
      ),
      
      # Aba Mapas
      tabItem(tabName = "mapas",
              fluidRow(
                box(title = "Mapa de Casos Confirmados - Brasil", width = 12, plotOutput("mapa_brasil"))
              ),
              fluidRow(
                box(title = "Mapa de Casos Confirmados - RJ", width = 12, plotOutput("mapa_rj"))
              )
      )
    )
  )
)

server <- function(input, output, session) {
  # Os dados devem ser carregados previamente e organizados conforme o script de preparação
  
  # Exemplos de outputs:
  output$casos_brasil <- renderValueBox({
    valueBox(value = formatC(casos_brasil, big.mark = ","), subtitle = "Casos no Brasil", icon = icon("globe"), color = "blue")
  })
  
  output$casos_rj <- renderValueBox({
    valueBox(value = formatC(casos_rj_total, big.mark = ","), subtitle = "Casos no RJ", icon = icon("map"), color = "teal")
  })
  
  output$casos_mun_rj <- renderValueBox({
    valueBox(value = formatC(casos_mun_rj_total, big.mark = ","), subtitle = "Casos no Mun. RJ", icon = icon("city"), color = "olive")
  })
  
  output$letalidade_brasil <- renderValueBox({
    valueBox(value = paste0(letalidade_brasil, "%"), subtitle = "Letalidade Brasil", icon = icon("heartbeat"), color = "red")
  })
  
  output$letalidade_rj <- renderValueBox({
    valueBox(value = paste0(letalidade_rj, "%"), subtitle = "Letalidade RJ", icon = icon("heartbeat"), color = "red")
  })
  
  output$letalidade_mun_rj <- renderValueBox({
    valueBox(value = paste0(letalidade_mun_rj, "%"), subtitle = "Letalidade Mun. RJ", icon = icon("heartbeat"), color = "red")
  })
  
  output$top_municipios <- DT::renderDataTable({ DT::datatable(top_municipios) })
  output$top_rj <- DT::renderDataTable({ DT::datatable(top_rj) })
  output$tabela_estados <- DT::renderDataTable({ DT::datatable(tabela_estados) })
  
  output$grafico_casos_dia <- renderPlot({
    ggplot(df_final, aes(x = dia, y = casosnovos, color = entidade)) +
      geom_point(size = 1.5) +
      geom_line() +
      labs(title = "Casos Novos por Dia", x = "Dia", y = "Casos Novos") +
      theme_minimal()
  })
  
  output$grafico_media_obitos <- renderPlot({
    ggplot(df_final, aes(x = dia, y = media_movel, color = entidade)) +
      geom_point(size = 1.3) +
      geom_line(size = 1) +
      labs(title = "Média Móvel de Óbitos", x = "Dia", y = "Óbitos") +
      theme_minimal()
  })
  
  output$grafico_acumulados_rj <- renderPlot({
    ggplot(dados_rj_completo) +
      geom_point(aes(x = dia, y = casos_acumulados), color = "blue") +
      geom_line(aes(x = dia, y = casos_acumulados), color = "blue") +
      geom_point(aes(x = dia, y = obitos_acumulados), color = "red") +
      geom_line(aes(x = dia, y = obitos_acumulados), color = "red") +
      labs(title = "Casos e Óbitos Acumulados RJ", x = "Dia", y = "Total Acumulado") +
      theme_minimal()
  })
  
  output$mapa_brasil <- renderPlot({
    ggplot(shape_brasil_dados) +
      geom_sf(aes(fill = casos_total), color = "white", size = 0.2) +
      scale_fill_gradient(low = "#deebf7", high = "#08519c", na.value = "grey90") +
      labs(title = "Casos Confirmados por Estado", fill = "Casos") +
      theme_minimal()
  })
  
  output$mapa_rj <- renderPlot({
    ggplot(mapa_rj_dados) +
      geom_sf(aes(fill = casos_total), color = "white", size = 0.2) +
      scale_fill_gradient(low = "#fee0d2", high = "#de2d26", na.value = "grey90") +
      labs(title = "Casos Confirmados por Município - RJ", fill = "Casos") +
      theme_minimal()
  })
}

shinyApp(ui, server)



