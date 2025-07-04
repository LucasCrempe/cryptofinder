import requests
import sqlite3
from datetime import datetime
import time
import os
from pathlib import Path

class ColetorDadosCripto:
    def __init__(self, db_path: str = "data/criptomoedas.db"):
        self.db_path = db_path
        self.arquivo_progresso = "data/ultima_pagina.txt"
        self.conn = None
        
        Path(self.db_path).parent.mkdir(exist_ok=True)
    
    def carregar_pagina_inicial(self) -> int:
        if os.path.exists(self.arquivo_progresso):
            try:
                with open(self.arquivo_progresso, 'r') as f:
                    return int(f.read().strip())
            except (ValueError, FileNotFoundError):
                pass
        return 1
    
    def salvar_progresso(self, pagina: int):
        Path(self.arquivo_progresso).parent.mkdir(exist_ok=True)
        with open(self.arquivo_progresso, 'w') as f:
            f.write(str(pagina))
    
    def inicializar_banco(self):
        try:
            self.conn = sqlite3.connect(self.db_path)
            cursor = self.conn.cursor()
            
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
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Erro ao inicializar banco: {e}")
            return False
    
    def processar_moeda(self, moeda_data: dict) -> tuple:
        return (
            moeda_data.get('id'),
            moeda_data.get('name'),
            moeda_data.get('symbol'),
            moeda_data.get('current_price'),
            moeda_data.get('price_change_percentage_24h'),
            moeda_data.get('market_cap'),
            datetime.utcnow().isoformat()
        )
    
    def coletar_dados(self):
        if not self.inicializar_banco():
            return
        
        pagina = self.carregar_pagina_inicial()
        total_inseridas = 0
        
        print("Iniciando coleta de dados da CoinGecko...")
        print(f"Começando da página {pagina}")
        
        while True:
            url = 'https://api.coingecko.com/api/v3/coins/markets'
            params = {
                'vs_currency': 'usd',
                'order': 'market_cap_desc',
                'per_page': 250,
                'page': pagina,
                'sparkline': False
            }
            
            print(f"Coletando página {pagina}...")
            
            try:
                resposta = requests.get(url, params=params, timeout=30)
                
                if resposta.status_code == 429:
                    print("Limite de requisições atingido. Aguardando...")
                    time.sleep(60)
                    continue
                
                if resposta.status_code != 200:
                    print(f"Erro HTTP {resposta.status_code}")
                    break
                
                dados = resposta.json()
                
                if not dados:
                    print("Coleta finalizada - sem mais dados.")
                    break
                
                cursor = self.conn.cursor()
                inseridas_pagina = 0
                
                for moeda in dados:
                    try:
                        dados_moeda = self.processar_moeda(moeda)
                        cursor.execute('''
                            INSERT OR REPLACE INTO moedas 
                            (id, nome, simbolo, preco_usd, variacao_24h, market_cap, ultima_atualizacao)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        ''', dados_moeda)
                        inseridas_pagina += 1
                    except Exception as e:
                        print(f"Erro ao processar moeda {moeda.get('id', 'unknown')}: {e}")
                
                self.conn.commit()
                total_inseridas += inseridas_pagina
                
                print(f"Página {pagina}: {inseridas_pagina} moedas processadas")
                
                pagina += 1
                self.salvar_progresso(pagina)
                time.sleep(3)  
                
            except requests.RequestException as e:
                print(f"Erro na requisição: {e}")
                break
            except Exception as e:
                print(f"Erro inesperado: {e}")
                break
        
        print(f"\nColeta finalizada. Total: {total_inseridas} moedas")
        
        if self.conn:
            self.conn.close()

if __name__ == "__main__":
    coletor = ColetorDadosCripto()
    coletor.coletar_dados()
