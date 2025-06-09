import sys
import sqlite3
import pandas as pd
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QComboBox, QDateEdit, QPushButton, QLabel, QTabWidget, QFrame
)
from PyQt6.QtCore import QDate
from datetime import datetime
import plotly.graph_objects as go
from PyQt6.QtWebEngineWidgets import QWebEngineView

# ===================
# Paleta de cores
# ===================
COLOR_BG       = "#151e1e"
COLOR_CARD     = "#181f20"
COLOR_TEXT     = "#76ff72"
COLOR_NEON     = "#00ffb2"
COLOR_TEXT_SEC = "#3afffc"
COLOR_NEG      = "#ff5b72"

DB_PATH = "Data/G2_Mercado.DB"

# ===================
# Funções utilitárias
# ===================
def get_acoes():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT sigla FROM Acao ORDER BY sigla", conn)
    conn.close()
    return df['sigla'].tolist()

def get_historico(sigla, data_ini, data_fim):
    conn = sqlite3.connect(DB_PATH)
    query = """
        SELECT h.data, h.abertura, h.maxima, h.minima, h.fechamento, h.volume
        FROM HistoricoAcao h
        JOIN Acao a ON h.acao_id = a.id
        WHERE a.sigla = ?
          AND h.data >= ?
          AND h.data <= ?
        ORDER BY h.data ASC
    """
    df = pd.read_sql_query(query, conn, params=(sigla, data_ini, data_fim))
    conn.close()
    df['data'] = pd.to_datetime(df['data'])
    return df

def make_candlestick(df):
    fig = go.Figure(
        data=[
            go.Candlestick(
                x=df['data'],
                open=df['abertura'],
                high=df['maxima'],
                low=df['minima'],
                close=df['fechamento'],
                name='Candlestick'
            )
        ]
    )
    fig.update_layout(
        title='Candlestick',
        xaxis_title='Data', yaxis_title='Preço',
        plot_bgcolor=COLOR_BG,
        paper_bgcolor=COLOR_BG,
        font_color=COLOR_TEXT
    )
    return fig.to_html(include_plotlyjs='cdn')

def make_fechamento(df):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['data'], y=df['fechamento'],
        mode='lines+markers', name='Fechamento',
        line=dict(color=COLOR_TEXT)
    ))
    fig.update_layout(
        title='Fechamento Diário',
        xaxis_title='Data', yaxis_title='Preço',
        plot_bgcolor=COLOR_BG,
        paper_bgcolor=COLOR_BG,
        font_color=COLOR_TEXT
    )
    return fig.to_html(include_plotlyjs='cdn')

def make_volume(df):
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df['data'], y=df['volume'],
        name='Volume', marker_color=COLOR_NEON
    ))
    fig.update_layout(
        title='Volume Negociado',
        xaxis_title='Data', yaxis_title='Volume',
        plot_bgcolor=COLOR_BG,
        paper_bgcolor=COLOR_BG,
        font_color=COLOR_TEXT
    )
    return fig.to_html(include_plotlyjs='cdn')

def make_media_movel(df, janela=20):
    df = df.copy()
    df['media_movel'] = df['fechamento'].rolling(janela).mean()
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['data'], y=df['fechamento'],
        mode='lines', name='Fechamento',
        line=dict(color=COLOR_TEXT)
    ))
    fig.add_trace(go.Scatter(
        x=df['data'], y=df['media_movel'],
        mode='lines', name=f'Média Móvel {janela} dias',
        line=dict(color=COLOR_TEXT_SEC)
    ))
    fig.update_layout(
        title=f'Média Móvel ({janela} dias)',
        xaxis_title='Data', yaxis_title='Preço',
        plot_bgcolor=COLOR_BG,
        paper_bgcolor=COLOR_BG,
        font_color=COLOR_TEXT
    )
    return fig.to_html(include_plotlyjs='cdn')

def maior_alta_baixa(df):
    if len(df) == 0:
        return 0, 0, 0
    alta = (df['fechamento'] - df['abertura']).max()
    baixa = (df['fechamento'] - df['abertura']).min()
    variacao = ((df['fechamento'].iloc[-1] / df['fechamento'].iloc[0]) - 1) * 100 if df['fechamento'].iloc[0] != 0 else 0
    return alta, baixa, variacao

def make_highlight_card(titulo, valor, cor=COLOR_TEXT):
    card = QFrame()
    card.setStyleSheet(f"""
        background-color: {COLOR_CARD};
        color: {cor};
        border: 2px solid {cor};
        border-radius: 12px;
        padding: 16px;
    """)
    layout = QVBoxLayout()
    card.setLayout(layout)
    label_titulo = QLabel(titulo)
    label_titulo.setStyleSheet(f"font-size: 15px; color: {cor}; font-weight: bold;")
    label_valor = QLabel(valor)
    label_valor.setStyleSheet(f"font-size: 25px; color: {cor}; font-weight: bold;")
    layout.addWidget(label_titulo)
    layout.addWidget(label_valor)
    card.setFixedWidth(180)
    return card

# ===================
# Classe principal da Janela
# ===================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Análise Dados de Ações")
        self.resize(1280, 900)
        self.setStyleSheet(f"background-color: {COLOR_BG}; color: {COLOR_TEXT};")
        widget = QWidget()
        main_layout = QVBoxLayout()
        widget.setLayout(main_layout)
        self.setCentralWidget(widget)

        # Top Bar
        topbar = QHBoxLayout()
        logo = QLabel("📈 Análise Dados de Ações")
        logo.setStyleSheet(f"font-size: 28px; color: {COLOR_TEXT}; font-weight: bold;")
        topbar.addWidget(logo)
        topbar.addStretch()
        label_acao = QLabel("Ação:")
        label_acao.setStyleSheet(f"font-size: 18px; color: {COLOR_TEXT_SEC};")
        self.cbo_acao = QComboBox()
        self.cbo_acao.addItems(get_acoes())
        self.cbo_acao.setStyleSheet(f"background-color: {COLOR_CARD}; color: {COLOR_TEXT};")
        label_ini = QLabel("Início:")
        label_ini.setStyleSheet(f"font-size: 18px; color: {COLOR_TEXT_SEC};")
        self.date_ini = QDateEdit()
        self.date_ini.setCalendarPopup(True)
        self.date_ini.setDate(QDate.currentDate().addDays(-365))
        self.date_ini.setStyleSheet(f"background-color: {COLOR_CARD}; color: {COLOR_TEXT};")
        label_fim = QLabel("Fim:")
        label_fim.setStyleSheet(f"font-size: 18px; color: {COLOR_TEXT_SEC};")
        self.date_fim = QDateEdit()
        self.date_fim.setCalendarPopup(True)
        self.date_fim.setDate(QDate.currentDate())
        self.date_fim.setStyleSheet(f"background-color: {COLOR_CARD}; color: {COLOR_TEXT};")
        self.btn_atualizar = QPushButton("Atualizar Gráficos")
        self.btn_atualizar.setStyleSheet(
            f"background-color: {COLOR_NEON}; color: {COLOR_BG}; font-weight: bold;"
        )
        self.btn_atualizar.clicked.connect(self.gerar_graficos)

        for w in [label_acao, self.cbo_acao, label_ini, self.date_ini, label_fim, self.date_fim, self.btn_atualizar]:
            topbar.addWidget(w)
        main_layout.addLayout(topbar)

        # Highlight cards
        self.hl_layout = QHBoxLayout()
        main_layout.addLayout(self.hl_layout)

        # Tabs para gráficos
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabBar::tab {{ background: {COLOR_CARD}; color: {COLOR_TEXT}; font-size: 18px; padding: 10px;}}
            QTabBar::tab:selected {{ background: {COLOR_NEON}; color: {COLOR_BG};}}
        """)
        main_layout.addWidget(self.tabs, stretch=1)
        self.graph_views = []
        for nome in ['Candlestick', 'Fechamento', 'Volume', 'Média Móvel']:
            view = QWebEngineView()
            self.tabs.addTab(view, nome)
            self.graph_views.append(view)

        self.gerar_graficos()

    def gerar_graficos(self):
        sigla = self.cbo_acao.currentText()
        data_ini = self.date_ini.date().toString("yyyy-MM-dd")
        data_fim = self.date_fim.date().toString("yyyy-MM-dd")
        df = get_historico(sigla, data_ini, data_fim)
        # Atualizar highlights
        alta, baixa, variacao = maior_alta_baixa(df)
        # Limpar e adicionar destaques
        for i in reversed(range(self.hl_layout.count())):
            item = self.hl_layout.itemAt(i)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
            else:
                self.hl_layout.removeItem(item)
        self.hl_layout.addWidget(make_highlight_card("Maior Alta", f"{alta:.2f}", COLOR_NEON))
        self.hl_layout.addWidget(make_highlight_card("Maior Baixa", f"{baixa:.2f}", COLOR_NEG))
        self.hl_layout.addWidget(make_highlight_card("Variação (%)", f"{variacao:.2f}%", COLOR_TEXT))
        self.hl_layout.addStretch()
        # Gráficos
        if len(df) == 0:
            for v in self.graph_views:
                v.setHtml(f"<h3 style='color:{COLOR_NEG}'>Nenhum dado encontrado!</h3>")
            return
        self.graph_views[0].setHtml(make_candlestick(df))
        self.graph_views[1].setHtml(make_fechamento(df))
        self.graph_views[2].setHtml(make_volume(df))
        self.graph_views[3].setHtml(make_media_movel(df, janela=20))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
