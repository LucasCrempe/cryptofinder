import sqlite3
import pandas as pd
import pickle
import re
from typing import Dict, List, Set
from pathlib import Path

class ConstrutorIndiceInvertido:
    def __init__(self, db_path: str = "data/criptomoedas.db"):
        self.db_path = db_path
        self.indice = {}
        
        self.stopwords = {
            'de', 'da', 'do', 'das', 'dos', 'a', 'o', 'as', 'os', 'e', 'em', 'para',
            'com', 'por', 'um', 'uma', 'uns', 'umas', 'na', 'no', 'nas', 'nos'
        }
    
    def carregar_dados(self) -> pd.DataFrame:
        try:
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql_query("SELECT id, nome, simbolo FROM moedas", conn)
            conn.close()
            return df
        except Exception as e:
            print(f"Erro ao carregar dados: {e}")
            return pd.DataFrame()
    
    def preprocessar_texto(self, texto: str) -> List[str]:
        if not texto or pd.isna(texto):
            return []
        
        texto_limpo = re.sub(r'[^a-zA-Z0-9\s]', ' ', texto.lower())
        
        tokens = texto_limpo.split()
        
        tokens_filtrados = [
            token for token in tokens 
            if len(token) >= 1 and token not in self.stopwords and token.isalnum()
        ]
        
        return tokens_filtrados
    
    def construir_indice(self) -> Dict[str, List[str]]:
        df = self.carregar_dados()
        
        if df.empty:
            print("Nenhum dado encontrado.")
            return {}
        
        indice_temp = {}
        
        print(f"Processando {len(df)} registros...")
        
        for _, linha in df.iterrows():
            termos_nome = self.preprocessar_texto(linha['nome'])
            termos_simbolo = self.preprocessar_texto(linha['simbolo'])
            termos_id = self.preprocessar_texto(linha['id'])
            
            if linha['simbolo'] and not pd.isna(linha['simbolo']):
                termos_simbolo.append(linha['simbolo'].lower().strip())
            
            todos_termos = termos_nome + termos_simbolo + termos_id
            
            for termo in todos_termos:
                if termo not in indice_temp:
                    indice_temp[termo] = set()
                indice_temp[termo].add(linha['id'])
        
        self.indice = {termo: list(ids) for termo, ids in indice_temp.items()}
        
        print(f"Índice criado com {len(self.indice)} termos únicos.")
        return self.indice
    
    def salvar_indice(self, arquivo: str = "data/indice_invertido.pkl"):
        Path(arquivo).parent.mkdir(exist_ok=True)
        
        try:
            with open(arquivo, "wb") as f:
                pickle.dump(self.indice, f, protocol=pickle.HIGHEST_PROTOCOL)
            print(f"Índice salvo em: {arquivo}")
            return True
        except Exception as e:
            print(f"Erro ao salvar índice: {e}")
            return False
    
    def executar(self):
        print("Construindo índice invertido...")
        
        if self.construir_indice():
            if self.salvar_indice():
                print("Processo concluído com sucesso.")
            else:
                print("Erro ao salvar o índice.")
        else:
            print("Erro ao construir o índice.")

if __name__ == "__main__":
    construtor = ConstrutorIndiceInvertido()
    construtor.executar()
