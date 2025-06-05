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

# --- CONECTAR E LER ---
conn <- dbConnect(SQLite(), "Data/G2.db")
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
casos_brasil_total <- sum(casos_completos$casosnovos, na.rm = TRUE)
obitos_brasil_total <- sum(casos_completos$mortesnovas, na.rm = TRUE)
pop_brasil <- sum(estados$populacao, na.rm = TRUE)
letalidade_brasil <- round((obitos_brasil_total / casos_brasil_total) * 100, 2)
mortalidade_brasil <- round((obitos_brasil_total / pop_brasil), 6)  # Mostra valor decimal tipo 0.00065


# 🟦 Estado RJ
casos_rj <- casos_completos %>% filter(uf == "RJ")
casos_rj_total <- sum(casos_rj$casosnovos, na.rm = TRUE)
obitos_rj_total <- sum(casos_rj$mortesnovas, na.rm = TRUE)
pop_rj <- estados %>% filter(uf == "RJ") %>% pull(populacao)
letalidade_rj <- round((obitos_rj_total / casos_rj_total) * 100, 2)
mortalidade_rj <- round((obitos_rj_total / pop_rj) , 6)

# 🏙️ Município RJ
casos_mun_rj <- casos_completos %>% filter(codigomunicipal == "3304557")
casos_mun_rj_total <- sum(casos_mun_rj$casosnovos, na.rm = TRUE)
obitos_mun_rj_total <- sum(casos_mun_rj$mortesnovas, na.rm = TRUE)
pop_mun_rj <- municipios %>% filter(codigomunicipal == "3304557") %>% pull(populacao)
letalidade_mun_rj <- round((obitos_mun_rj_total / casos_mun_rj_total) * 100, 2)
mortalidade_mun_rj <- round((obitos_mun_rj_total / pop_mun_rj) , 6)

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

casos_regiao <- casos_completos %>%
  group_by(codigoregiao, nomeregiao) %>%
  summarise(
    casos_total = sum(casosnovos, na.rm = TRUE),
    .groups = "drop"
  ) %>%
  left_join(regioes %>% select(codigoregiao, populacao), by = "codigoregiao") %>%
  mutate(taxa_incidencia = casos_total * 100 / populacao)

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
    Mortalidade = Óbitos / Populacao
  ) %>%
  arrange(uf) %>%
  select(UF = uf, Confirmado, Óbitos, Letalidade, Mortalidade)

#========================== CASOS POR DIA

# Série de dias completos
datas_completas <- seq(min(casos_completos$data), max(casos_completos$data), by = "1 day")

# Casos diários Brasil
casos_brasil_diario <- casos_completos %>%
  group_by(data) %>%
  summarise(casosnovos = sum(casosnovos, na.rm = TRUE), .groups = "drop") %>%
  mutate(entidade = "Brasil")

df_brasil_casos <- data.frame(data = datas_completas) %>%
  left_join(casos_brasil_diario, by = "data") %>%
  mutate(
    casosnovos = ifelse(is.na(casosnovos), 0, casosnovos),
    entidade = "Brasil"
  )

# Casos diários RJ
casos_rj_diario <- casos_completos %>%
  filter(uf == "RJ") %>%
  group_by(data) %>%
  summarise(casosnovos = sum(casosnovos, na.rm = TRUE), .groups = "drop") %>%
  mutate(entidade = "RJ")

df_rj_casos <- data.frame(data = datas_completas) %>%
  left_join(casos_rj_diario, by = "data") %>%
  mutate(
    casosnovos = ifelse(is.na(casosnovos), 0, casosnovos),
    entidade = "RJ"
  )

# Data frame final para gráfico de casos novos por dia
df_final_casos <- bind_rows(df_brasil_casos, df_rj_casos) %>%
  arrange(data) %>%
  mutate(dia = row_number())

#========================= MEDIA MOVEL DE OBITOS

# Óbitos diários Brasil
obitos_brasil_diario <- casos_completos %>%
  group_by(data) %>%
  summarise(obitos = sum(mortesnovas, na.rm = TRUE), .groups = "drop") %>%
  mutate(entidade = "Brasil")

df_brasil_obitos <- data.frame(data = datas_completas) %>%
  left_join(obitos_brasil_diario, by = "data") %>%
  mutate(
    obitos = ifelse(is.na(obitos), 0, obitos),
    entidade = "Brasil"
  )

# Óbitos diários RJ
obitos_rj_diario <- casos_completos %>%
  filter(uf == "RJ") %>%
  group_by(data) %>%
  summarise(obitos = sum(mortesnovas, na.rm = TRUE), .groups = "drop") %>%
  mutate(entidade = "RJ")

df_rj_obitos <- data.frame(data = datas_completas) %>%
  left_join(obitos_rj_diario, by = "data") %>%
  mutate(
    obitos = ifelse(is.na(obitos), 0, obitos),
    entidade = "RJ"
  )

# Data frame final para gráfico de média móvel de óbitos
df_final_obitos <- bind_rows(df_brasil_obitos, df_rj_obitos) %>%
  arrange(data) %>%
  group_by(entidade) %>%
  mutate(
    media_movel = zoo::rollmean(obitos, k = 6, align = "right", fill = 0),
    dia = row_number()
  ) %>%
  ungroup()

#======================== CASOS ACUMULADOS POR DIA
dados_rj <- casos_completos %>%
  filter(uf == "RJ") %>%
  group_by(data) %>%
  summarise(
    casosnovos = sum(casosnovos, na.rm = TRUE),
    mortesnovas = sum(mortesnovas, na.rm = TRUE),
    .groups = "drop"
  )

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

#=================== MAPA DE CASOS NO BRASIL
casos_estado <- casos_completos %>%
  group_by(uf) %>%
  summarise(casos_total = sum(casosnovos, na.rm = TRUE), .groups = "drop")

shape_brasil <- st_read("Mapas/BR_UF_2022.shp", quiet = TRUE)
shape_brasil_dados <- shape_brasil %>%
  left_join(casos_estado, by = c("SIGLA_UF" = "uf"))

#============ MUNICIPIOS DO RJ
casos_municipio_rj <- casos_completos %>%
  filter(codigoestadual == "33") %>%  # RJ = 33
  group_by(codigomunicipal) %>%
  summarise(casos_total = sum(casosnovos, na.rm = TRUE), .groups = "drop")

mapa_rj <- st_read("Mapas/RJ_Municipios_2022.shp", quiet = TRUE)
mapa_rj_dados <- mapa_rj %>%
  mutate(codigomunicipal = as.character(CD_MUN)) %>%
  left_join(casos_municipio_rj, by = "codigomunicipal")

#================Shiny
ui <- dashboardPage(
  dashboardHeader(title = "Painel COVID-19 - Grupo 2"),
  dashboardSidebar(
    sidebarMenu(
      menuItem("Painel Geral", tabName = "painel_geral", icon = icon("dashboard")),
      menuItem("Painel de Casos Diários", tabName = "casos_diarios", icon = icon("chart-line"))
    )
  ),
  dashboardBody(
    tags$head(
      tags$style(HTML("
          .box, .value-box, .small-box {
          border-radius: 16px !important;
          box-shadow: 0 2px 8px rgba(0,0,0,0.07);
          }
        table.dataTable {
          font-size: 13px !important;
    }
      "))
    ),
    tabItems(
      # PAINEL GERAL
      tabItem(tabName = "painel_geral",
              fluidRow(
                box(width = 3, title = NULL, status = "primary",
                    h4("Total de casos confirmados"),
                    tags$ul(
                      tags$li("Brasil: ", span(textOutput("casos_brasil"), style="color:blue")),
                      tags$li("Estado do Rio de Janeiro: ", span(textOutput("casos_rj"), style="color:blue")),
                      tags$li("Cidade do Rio de Janeiro: ", span(textOutput("casos_mun_rj"), style="color:blue"))
                    )
                ),
                box(width = 3, title = NULL, status = "danger",
                    h4("Total de óbitos"),
                    tags$ul(
                      tags$li("Brasil: ", span(textOutput("obitos_brasil"), style="color:orange")),
                      tags$li("Estado do Rio de Janeiro: ", span(textOutput("obitos_rj"), style="color:orange")),
                      tags$li("Cidade do Rio de Janeiro: ", span(textOutput("obitos_mun_rj"), style="color:orange"))
                    )
                ),
                box(width = 3, title = NULL, status = "warning",
                    h4("Letalidade (óbitos / casos confirmados)"),
                    tags$ul(
                      tags$li("Brasil: ", span(textOutput("letalidade_brasil"), style="color:purple")),
                      tags$li("Estado do Rio de Janeiro: ", span(textOutput("letalidade_rj"), style="color:purple")),
                      tags$li("Cidade do Rio de Janeiro: ", span(textOutput("letalidade_mun_rj"), style="color:purple"))
                    )
                ),
                box(width = 3, title = NULL, status = "info",
                    h4("Mortalidade (óbitos / habitantes)"),
                    tags$ul(
                      tags$li("Brasil: ", span(textOutput("mortalidade_brasil"), style="color:red")),
                      tags$li("Estado do Rio de Janeiro: ", span(textOutput("mortalidade_rj"), style="color:red")),
                      tags$li("Cidade do Rio de Janeiro: ", span(textOutput("mortalidade_mun_rj"), style="color:red"))
                    )
                )
              ),
              fluidRow(
                column(width=6,
                       box(width=NULL, title="Casos no Brasil", status="primary",
                           plotOutput("mapa_brasil", height=200)),
                       box(width=NULL, title="Casos no Estado do Rio de Janeiro", status="primary",
                           plotOutput("mapa_rj", height=200))
                ),
                column(width=3,
                       box(width=NULL, title="Casos por região", status="primary",
                           plotOutput("grafico_regiao", height=200)),
                       box(width=NULL, title="Casos por estados da região Sudeste", status="primary",
                           plotOutput("grafico_sudeste", height=200))
                ),
                column(width=3,
                       box(width=NULL, title="Top 10 cidades do Brasil", status="primary",
                           DTOutput("top_municipios_brasil", height=200)),
                       box(width=NULL, title="Top 10 cidades ERJ", status="primary",
                           DTOutput("top_municipios_rj", height=200))
                )
              )
      ),
      # PAINEL DE CASOS DIÁRIOS
      tabItem(tabName = "casos_diarios",
              fluidRow(
                column(width=8,
                       box(width=NULL, title="Casos novos por dia", status="primary",
                           plotOutput("grafico_casos_dia", height=160)),
                       box(width=NULL, title="Média móvel de óbitos do Brasil e do Estado do Rio de Janeiro", status="primary",
                           plotOutput("grafico_media_obitos", height=160)),
                       box(width=NULL, title="Casos acumulados e óbitos do Estado do Rio de Janeiro", status="primary",
                           plotOutput("grafico_acumulados_rj", height=160))
                ),
                column(width=4,
                       box(width=NULL, title="Casos por Estado", status="primary",
                           DTOutput("tabela_estados", height=700))
                )
              )
      )
    )
  )
)

server <- function(input, output, session) {
  # Indicadores
  output$casos_brasil <- renderText({ format(casos_brasil_total, big.mark = ".", scientific = FALSE) })
  output$casos_rj <- renderText({ format(casos_rj_total, big.mark = ".", scientific = FALSE) })
  output$casos_mun_rj <- renderText({ format(casos_mun_rj_total, big.mark = ".", scientific = FALSE) })
  output$obitos_brasil <- renderText({ format(obitos_brasil_total, big.mark = ".", scientific = FALSE) })
  output$obitos_rj <- renderText({ format(obitos_rj_total, big.mark = ".", scientific = FALSE) })
  output$obitos_mun_rj <- renderText({ format(obitos_mun_rj_total, big.mark = ".", scientific = FALSE) })
  output$letalidade_brasil <- renderText({ paste0(letalidade_brasil, "%") })
  output$letalidade_rj <- renderText({ paste0(letalidade_rj, "%") })
  output$letalidade_mun_rj <- renderText({ paste0(letalidade_mun_rj, "%") })
  output$mortalidade_brasil <- renderText({ format(mortalidade_brasil, big.mark = ".", scientific = FALSE) })
  output$mortalidade_rj <- renderText({ format(mortalidade_rj, big.mark = ".", scientific = FALSE) })
  output$mortalidade_mun_rj <- renderText({ format(mortalidade_mun_rj, big.mark = ".", scientific = FALSE) })
  
  output$mapa_brasil <- renderPlot({
    ggplot(shape_brasil_dados) +
      geom_sf(aes(fill = casos_total), color = "white", size = 0.2) +
      scale_fill_gradient(low = "#deebf7", high = "#08519c", na.value = "grey90") +
      labs(fill = "Casos") +
      theme_minimal()
  })
  
  output$mapa_rj <- renderPlot({
    ggplot(mapa_rj_dados) +
      geom_sf(aes(fill = casos_total), color = "white", linewidth = 0.2) +
      scale_fill_gradient(low = "#fee0d2", high = "#de2d26", na.value = "grey90") +
      labs(
        title = "Casos Confirmados Acumulados por Município – Estado do RJ",
        fill = "Casos acumulados"
      ) +
      theme_minimal()
  })
  
  output$grafico_regiao <- renderPlot({
    df <- casos_regiao
    ggplot(df, aes(x = reorder(nomeregiao, -taxa_incidencia), y = taxa_incidencia, fill = nomeregiao)) +
      geom_bar(stat = "identity", width = 0.7, show.legend = FALSE) +
      coord_flip() +
      labs(
        x = "Região",
        y = "Taxa de Incidência (%)"
      ) +
      theme_minimal()
  })
  
  casos_sudeste <- tabela_estados %>%
    filter(UF %in% c("RJ", "SP", "MG", "ES"))
  output$grafico_sudeste <- renderPlot({
    df <- casos_sudeste
    ggplot(df, aes(x = reorder(UF, Confirmado), y = Confirmado, fill = UF)) +
      geom_bar(stat = "identity", width = 0.7, show.legend = FALSE) +
      coord_flip() +
      labs(
        x = "Estado",
        y = "Total de Casos"
      ) +
      theme_minimal()
  })
  
  output$top_municipios_brasil <- renderDT({
    df <- top_municipios
    df$Taxa <- round(df$Taxa, 2)
    df$Letalidade <- round(df$Letalidade, 2)
    df$Mortalidade <- round(df$Mortalidade, 6)
    datatable(
      df,
      colnames = c("UF", "Mun.", "Taxa", "Let", "Mort"),
      options = list(pageLength = 10, scrollX = TRUE, scrollY = "150px", dom = 't'),
      style = "bootstrap"
    )
  })
  output$top_municipios_rj <- renderDT({
    df <- top_rj
    df$Taxa <- round(df$Taxa, 2)
    df$Letalidade <- round(df$Letalidade, 2)
    df$Mortalidade <- round(df$Mortalidade, 6)
    datatable(
      df,
      colnames = c("UF", "Mun.", "Taxa", "Let", "Mort"),
      options = list(pageLength = 10, scrollX = TRUE, scrollY = "150px", dom = 't'),
      style = "bootstrap"
    )
  })
  
  output$grafico_casos_dia <- renderPlot({
    ggplot(df_final_casos, aes(x = dia, y = casosnovos, color = entidade)) +
      geom_point(size = 1.5) + geom_line() +
      labs( x = "Dia", y = "Casos Novos") +
      theme_minimal()
  })
  
  output$grafico_media_obitos <- renderPlot({
    ggplot(df_final_obitos, aes(x = dia, y = media_movel, color = entidade)) +
      geom_point(size = 1.3) + geom_line(size = 1) +
      labs(x = "Dia", y = "Óbitos") +
      theme_minimal()
  })
  
  output$grafico_acumulados_rj <- renderPlot({
    ggplot(dados_rj_completo) +
      geom_point(aes(x = dia, y = casos_acumulados), color = "blue", size = 1.5) +
      geom_line(aes(x = dia, y = casos_acumulados), color = "blue", linewidth = 1) +
      geom_point(aes(x = dia, y = obitos_acumulados), color = "red", size = 1.5) +
      geom_line(aes(x = dia, y = obitos_acumulados), color = "red", linewidth = 1) +
      labs(
        title = "Casos e Óbitos Acumulados RJ",
        x = "Dia",
        y = "Total Acumulado"
      ) +
      theme_minimal()
  })
  
  output$tabela_estados <- renderDT({
    df <- tabela_estados
    df$Letalidade <- round(df$Letalidade, 2)
    df$Mortalidade <- format(round(df$Mortalidade , 10), scientific = F)
    datatable(
      df,
      options = list(dom = 't', scrollY = "500px", ordering = TRUE, pageLength = nrow(df)),
      style = "bootstrap"
    )
  })
}

shinyApp(ui, server)
