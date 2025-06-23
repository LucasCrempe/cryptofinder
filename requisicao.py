import requests
import sqlite3
from datetime import datetime
import time
import os

# === Caminho do arquivo de controle de progresso ===
ARQUIVO_PAGINA = 'ultima_pagina.txt'

# === Função para carregar página inicial ===
def carregar_pagina_inicial():
    if os.path.exists(ARQUIVO_PAGINA):
        with open(ARQUIVO_PAGINA, 'r') as f:
            return int(f.read().strip())
    return 1  # começa do zero se não tiver

# === Função para salvar página atual ===
def salvar_pagina(pagina):
    with open(ARQUIVO_PAGINA, 'w') as f:
        f.write(str(pagina))

# === Conectar ao banco de dados ===
conn = sqlite3.connect('criptomoedas.db')
cursor = conn.cursor()

# === Criar tabela se não existir ===
cursor.execute('''
    CREATE TABLE IF NOT EXISTS moedas (
        id TEXT PRIMARY KEY,
        nome TEXT,
        simbolo TEXT,
        preco_usd REAL,
        variacao_24h REAL,
        market_cap REAL,
        ultima_atualizacao TEXT
    )
''')
conn.commit()

# === Iniciar a partir da última página salva ===
pagina = carregar_pagina_inicial()
total_inseridas = 0

while True:
    url = 'https://api.coingecko.com/api/v3/coins/markets'
    params = {
        'vs_currency': 'usd',
        'order': 'market_cap_desc',
        'per_page': 250,
        'page': pagina,
        'sparkline': False
    }

    print(f'📥 Buscando página {pagina}...')
    resposta = requests.get(url, params=params)

    if resposta.status_code == 429:
        print("⏳ Limite de requisições excedido. Aguardando 1 minuto...")
        time.sleep(60)
        continue

    if resposta.status_code != 200:
        print(f"❌ Erro na requisição: {resposta.status_code}")
        break

    dados = resposta.json()
    if not dados:
        print("✅ Todas as moedas foram carregadas.")
        break

    inseridas_esta_pagina = 0
    for moeda in dados:
        cursor.execute('''
            INSERT OR REPLACE INTO moedas 
            (id, nome, simbolo, preco_usd, variacao_24h, market_cap, ultima_atualizacao)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            moeda['id'],
            moeda['name'],
            moeda['symbol'],
            moeda['current_price'],
            moeda['price_change_percentage_24h'],
            moeda['market_cap'],
            datetime.utcnow().isoformat()
        ))
        inseridas_esta_pagina += 1
        total_inseridas += 1

    conn.commit()
    print(f"✅ Página {pagina} processada ({inseridas_esta_pagina} moedas).")
    pagina += 1
    salvar_pagina(pagina)  # Salva o progresso
    time.sleep(3)

print(f"\n🚀 Total de moedas inseridas ou atualizadas: {total_inseridas}")
conn.close()
