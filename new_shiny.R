# -*- coding: utf-8 -*-

library(shiny)
library(shinydashboard)

# --- Definição dos Placeholders (Textos de exemplo) ---
# Usamos esta abordagem para não poluir o layout com textos longos.
placeholder_texts <- list(
  metricas = "<XXX>",
  mapa_brasil = "<Mapa do Brasil por estados com padrão de cor degradê baseado no total de casos confirmados até o momento.>",
  mapa_rj = "<Mapa do RJ por cidades com padrão de cor degradê baseado no total de casos confirmados até o momento>",
  grafico_regiao = "<Gráfico de setores por região do Brasil com o % de casos confirmados (acumulados) de cada região. O gráfico deverá apresentar legenda.>",
  grafico_sudeste = "<Gráfico de setores por estados e % do total de casos confirmados (acumulados) de cada um com legenda.>",
  tabela_brasil = "<Tabela com 5 colunas: UF, Nome, Taxa, Letalidade e Mortalidade...>",
  tabela_rj = "<Tabela com 4 colunas: Nome, Taxa, Letalidade e Mortalidade...>",
  grafico_casos_novos = "<Gráfico de dispersão, tendo os pontos ligados, com o eixo X representando os dias e o eixo Y o total de casos novos...>",
  grafico_media_movel = "<Gráfico de dispersão formado pela média móvel com uma janela de 6 dias (dia atual + 5 anteriores)...>",
  grafico_acumulados = "<Gráfico de dispersão, tendo os pontos ligados, com o eixo X representando os dias e o eixo Y o total de casos acumulados...>",
  tabela_estados = "<Tabela com 5 colunas: UF do estado, Confirmado, Óbitos, Letalidade e Mortalidade...>"
)

# --- Função auxiliar para criar conteúdo de métrica ---
metric_content <- function(items) {
  # Cria uma lista de tags HTML para os itens da métrica
  lapply(items, function(item) {
    tags$li(
      item,
      tags$br(),
      tags$span(class = "placeholder-text", placeholder_texts$metricas)
    )
  })
}

# --- Interface do Utilizador (UI) ---
ui <- dashboardPage(
  skin = "blue", # Define o tema de cor principal
  dashboardHeader(title = "Painel de Monitoramento"),
  
  # --- Barra Lateral com os menus de navegação ---
  dashboardSidebar(
    sidebarMenu(
      id = "tabs",
      menuItem("Página 1", tabName = "page1", icon = icon("tachometer-alt")),
      menuItem("Página 2", tabName = "page2", icon = icon("chart-line"))
    )
  ),
  
  # --- Corpo do Painel ---
  dashboardBody(
    # CSS personalizado para replicar o design (bordas azuis, etc.)
    tags$head(
      tags$style(HTML("
        /* Adiciona a borda azul a todas as caixas (boxes) */
        .box {
          border: 2px solid #4a90e2;
        }
        /* Remove a sombra padrão para um visual mais limpo */
        .box.box-solid {
          box-shadow: none;
        }
        /* Estilo para o texto do placeholder */
        .placeholder-text {
          color: #4a90e2;
          font-family: 'Courier New', Courier, monospace;
          font-size: 0.9rem;
        }
        /* Divisória tracejada */
        .custom-hr {
          border-top: 2px dashed #ccc;
          margin-top: 1rem;
          margin-bottom: 1rem;
        }
      "))
    ),
    
    # --- Conteúdo das abas ---
    tabItems(
      # --- Conteúdo da Página 1 ---
      tabItem(tabName = "page1",
              # Linha de Métricas Superior
              fluidRow(
                box(title = "Total de casos confirmados", solidHeader = TRUE, width = 3, status = "primary", tags$ul(metric_content(c("Brasil", "Estado do Rio de Janeiro", "Cidade do Rio de Janeiro")))),
                box(title = "Total de óbitos", solidHeader = TRUE, width = 3, status = "primary", tags$ul(metric_content(c("Brasil", "Estado do Rio de Janeiro", "Cidade do Rio de Janeiro")))),
                box(title = "Letalidade (...)", solidHeader = TRUE, width = 3, status = "primary", tags$ul(metric_content(c("Brasil", "Estado do Rio de Janeiro", "Cidade do Rio de Janeiro")))),
                box(title = "Mortalidade (...)", solidHeader = TRUE, width = 3, status = "primary", tags$ul(metric_content(c("Brasil", "Estado do Rio de Janeiro", "Cidade do Rio de Janeiro"))))
              ),
              
              # Grid Principal de Conteúdo
              fluidRow(
                column(width = 4,
                       box(title = "Mapas", solidHeader = TRUE, status = "primary", width = NULL,
                           h4("Casos no Brasil", class="card-title"),
                           p(class = "placeholder-text", placeholder_texts$mapa_brasil),
                           hr(class="custom-hr"),
                           h4("Casos no Estado do Rio de Janeiro", class="card-title"),
                           p(class = "placeholder-text", placeholder_texts$mapa_rj)
                       )
                ),
                column(width = 4,
                       box(title = "Gráficos de Setores", solidHeader = TRUE, status = "primary", width = NULL,
                           h4("Casos por região", class="card-title"),
                           p(class = "placeholder-text", placeholder_texts$grafico_regiao),
                           hr(class="custom-hr"),
                           h4("Casos por estados da região Sudeste", class="card-title"),
                           p(class = "placeholder-text", placeholder_texts$grafico_sudeste)
                       )
                ),
                column(width = 4,
                       box(title = "10 cidades do Brasil com maior taxa", solidHeader = TRUE, status = "primary", width = NULL, p(class = "placeholder-text", placeholder_texts$tabela_brasil)),
                       box(title = "10 cidades do RJ com maior taxa", solidHeader = TRUE, status = "primary", width = NULL, p(class = "placeholder-text", placeholder_texts$tabela_rj))
                )
              )
      ),
      
      # --- Conteúdo da Página 2 ---
      tabItem(tabName = "page2",
              fluidRow(
                # Coluna Esquerda com 3 gráficos empilhados
                column(width = 6,
                       box(title = "Casos novos por dia", solidHeader = TRUE, status = "primary", width = NULL, p(class = "placeholder-text", placeholder_texts$grafico_casos_novos)),
                       box(title = "Média móvel de óbitos", solidHeader = TRUE, status = "primary", width = NULL, p(class = "placeholder-text", placeholder_texts$grafico_media_movel)),
                       box(title = "Casos acumulados e óbitos do RJ", solidHeader = TRUE, status = "primary", width = NULL, p(class = "placeholder-text", placeholder_texts$grafico_acumulados))
                ),
                # Coluna Direita com 1 tabela grande
                column(width = 6,
                       box(title = "Casos por Estado", solidHeader = TRUE, status = "primary", width = NULL, height = "85vh", # Altura ajustada para alinhar
                           p(class = "placeholder-text", placeholder_texts$tabela_estados)
                       )
                )
              )
      )
    )
  )
)

# --- Lógica do Servidor (vazia para este mock) ---
server <- function(input, output) {
  # Nenhuma lógica de servidor é necessária para um mock estático.
}

# --- Executa a Aplicação Shiny ---
shinyApp(ui, server)
