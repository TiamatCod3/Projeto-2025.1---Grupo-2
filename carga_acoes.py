import sqlite3
import yfinance as yf
from datetime import datetime, timedelta
import os

# Configurações de caminho
DB_PATH = os.path.join("Data", "G2_Mercado.db")
ACOES_PATH = os.path.join("Data", "Acoes.txt")
NAO_CARREGADAS_PATH = os.path.join("Data", "NaoCarregadas.txt")
# Criar arquivo de ações (se não existir)
if not os.path.exists(ACOES_PATH):
    with open(ACOES_PATH, "w") as f:
        f.write("\n".join([
            "PETR4.SA", "VALE3.SA", "ITUB4.SA",
            "BBDC4.SA", "ABEV3.SA", "BBAS3.SA"
        ]))
# Conectar ao banco
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
# Ativar foreign keys
cursor.execute("PRAGMA foreign_keys = ON")
# Criar tabelas
cursor.execute('''
CREATE TABLE IF NOT EXISTS Acao (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sigla TEXT UNIQUE,
    nome TEXT
)
''')
cursor.execute('''
CREATE TABLE IF NOT EXISTS HistoricoAcao (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data DATE,
    abertura REAL,
    fechamento REAL,
    maxima REAL,
    minima REAL,
    volume INTEGER,
    acao_id INTEGER,
    FOREIGN KEY (acao_id) REFERENCES Acao(id) ON DELETE CASCADE
)
''')
# Limpar dados antigos
cursor.execute("DELETE FROM HistoricoAcao")
cursor.execute("DELETE FROM Acao")
conn.commit()
# Ler ações
with open(ACOES_PATH, "r") as f:
    acoes = [linha.strip() for linha in f if linha.strip()]
# Datas
inicio = datetime.now().date() - timedelta(days=360)
fim = datetime.now().date()
nao_carregadas = []
# Coleta de dados
for sigla in acoes:
    try:
        ticker = yf.Ticker(sigla)
        nome = ticker.info.get("longName", "Desconhecido")
        cursor.execute("INSERT INTO Acao (sigla, nome) VALUES (?, ?)", (sigla, nome))
        acao_id = cursor.lastrowid

        df = ticker.history(start=inicio.isoformat(), end=fim.isoformat())
        for data, row in df.iterrows():
            cursor.execute("""
                INSERT INTO HistoricoAcao
                (data, abertura, fechamento, maxima, minima, volume, acao_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                data.date().isoformat(),
                row["Open"],
                row["Close"],
                row["High"],
                row["Low"],
                int(row["Volume"]),
                acao_id
            ))
        conn.commit()

    except Exception:
        nao_carregadas.append(sigla)
        conn.rollback()

# Registrar ações não carregadas
with open(NAO_CARREGADAS_PATH, "w") as f:
    f.write("\n".join(nao_carregadas))

conn.close()
print("Carga concluída com sucesso.")