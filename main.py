import sys
import sqlite3
import pandas as pd
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QComboBox, QDateEdit, QPushButton, QLabel, QTabWidget
)
from PyQt6.QtCore import QDate
from datetime import datetime
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from PyQt6.QtWebEngineWidgets import QWebEngineView

DB_PATH = "Data/G2_Mercado.DB"

# Função para carregar lista de ações do banco
def get_acoes():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT sigla FROM Acao ORDER BY sigla", conn)
    conn.close()
    return df['sigla'].tolist()

# Função para buscar dados históricos da ação selecionada
def get_historico(sigla, data_ini, data_fim):
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(
        f"""
        SELECT data, abertura, maximo, minimo, fechamento, volume
        FROM HistoricoAcao
        WHERE sigla = ?
          AND data >= ?
          AND data <= ?
        ORDER BY data ASC
        """,
        conn, params=(sigla, data_ini, data_fim)
    )
    conn.close()
    df['data'] = pd.to_datetime(df['data'])
    return df

# Função para gerar gráficos plotly e retornar como HTML
def make_candlestick(df):
    fig = go.Figure(
        data=[
            go.Candlestick(
                x=df['data'],
                open=df['abertura'],
                high=df['maximo'],
                low=df['minimo'],
                close=df['fechamento'],
                name='Candlestick'
            )
        ]
    )
    fig.update_layout(title='Candlestick', xaxis_title='Data', yaxis_title='Preço')
    return fig.to_html(include_plotlyjs='cdn')

def make_fechamento(df):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['data'], y=df['fechamento'],
        mode='lines+markers', name='Fechamento'
    ))
    fig.update_layout(title='Fechamento Diário', xaxis_title='Data', yaxis_title='Preço')
    return fig.to_html(include_plotlyjs='cdn')

def make_volume(df):
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df['data'], y=df['volume'],
        name='Volume'
    ))
    fig.update_layout(title='Volume Negociado', xaxis_title='Data', yaxis_title='Volume')
    return fig.to_html(include_plotlyjs='cdn')

def make_media_movel(df, janela=20):
    df['media_movel'] = df['fechamento'].rolling(janela).mean()
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['data'], y=df['fechamento'],
        mode='lines', name='Fechamento'
    ))
    fig.add_trace(go.Scatter(
        x=df['data'], y=df['media_movel'],
        mode='lines', name=f'Média Móvel {janela} dias'
    ))
    fig.update_layout(title=f'Média Móvel ({janela} dias)', xaxis_title='Data', yaxis_title='Preço')
    return fig.to_html(include_plotlyjs='cdn')

# Widget principal
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dashboard de Ações - G2")
        self.resize(1100, 900)
        widget = QWidget()
        layout = QVBoxLayout()
        self.setCentralWidget(widget)
        widget.setLayout(layout)

        # Seleção de ação e datas
        top_bar = QHBoxLayout()
        layout.addLayout(top_bar)
        top_bar.addWidget(QLabel("Ação:"))
        self.cbo_acao = QComboBox()
        self.cbo_acao.addItems(get_acoes())
        top_bar.addWidget(self.cbo_acao)
        top_bar.addWidget(QLabel("Data inicial:"))
        self.date_ini = QDateEdit()
        self.date_ini.setCalendarPopup(True)
        self.date_ini.setDate(QDate.currentDate().addDays(-365))
        top_bar.addWidget(self.date_ini)
        top_bar.addWidget(QLabel("Data final:"))
        self.date_fim = QDateEdit()
        self.date_fim.setCalendarPopup(True)
        self.date_fim.setDate(QDate.currentDate())
        top_bar.addWidget(self.date_fim)
        self.btn_atualizar = QPushButton("Atualizar Gráficos")
        self.btn_atualizar.clicked.connect(self.gerar_graficos)
        top_bar.addWidget(self.btn_atualizar)

        # Tabs para gráficos
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        # Criar 4 abas com QWebEngineView
        self.graph_views = []
        for nome in ['Candlestick', 'Fechamento', 'Volume', 'Média Móvel']:
            view = QWebEngineView()
            self.tabs.addTab(view, nome)
            self.graph_views.append(view)

        # Carregar gráficos iniciais
        self.gerar_graficos()

    def gerar_graficos(self):
        sigla = self.cbo_acao.currentText()
        data_ini = self.date_ini.date().toString("yyyy-MM-dd")
        data_fim = self.date_fim.date().toString("yyyy-MM-dd")
        df = get_historico(sigla, data_ini, data_fim)
        if len(df) == 0:
            for v in self.graph_views:
                v.setHtml("<h3>Nenhum dado encontrado!</h3>")
            return
        # Candlestick
        self.graph_views[0].setHtml(make_candlestick(df))
        # Fechamento Diário
        self.graph_views[1].setHtml(make_fechamento(df))
        # Volume
        self.graph_views[2].setHtml(make_volume(df))
        # Média Móvel
        self.graph_views[3].setHtml(make_media_movel(df))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
