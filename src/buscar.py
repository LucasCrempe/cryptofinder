import sqlite3
import sys
from typing import List, Tuple, Optional

class BuscadorCriptomoedas:
    def __init__(self, db_path: str = "data/criptomoedas.db"):
        self.db_path = db_path
        self.conn = None
        
    def conectar_banco(self) -> bool:
        try:
            self.conn = sqlite3.connect(self.db_path)
            return True
        except sqlite3.Error as e:
            print(f"Erro ao conectar com o banco: {e}")
            return False
    
    def fechar_conexao(self):
        if self.conn:
            self.conn.close()
    
    def buscar_moedas(self, tipo_busca: str, termo: str) -> List[Tuple]:
        if not self.conn:
            return []
        
        cursor = self.conn.cursor()
        
        if tipo_busca == "id":
            query = "SELECT * FROM moedas WHERE LOWER(id) LIKE ? ORDER BY market_cap DESC"
        elif tipo_busca == "nome":
            query = "SELECT * FROM moedas WHERE LOWER(nome) LIKE ? ORDER BY market_cap DESC"
        else:
            return []
        
        try:
            cursor.execute(query, (f"%{termo.lower()}%",))
            return cursor.fetchall()
        except sqlite3.Error:
            return []
    
    def formatar_valor(self, valor, tipo: str) -> str:
        if valor is None:
            return "N/A"
        
        try:
            if tipo == "preco":
                if valor < 0.01:
                    return f"${valor:.8f}"
                else:
                    return f"${valor:,.2f}"
            elif tipo == "variacao":
                return f"{valor:+.2f}%"
            elif tipo == "market_cap":
                if valor >= 1e9:
                    return f"${valor/1e9:.2f}B"
                elif valor >= 1e6:
                    return f"${valor/1e6:.2f}M"
                else:
                    return f"${valor:,.0f}"
        except (ValueError, TypeError):
            return "N/A"
        
        return str(valor)
    
    def exibir_detalhes_moeda(self, moeda: Tuple):
        print("\n" + "="*50)
        print("DETALHES DA CRIPTOMOEDA")
        print("="*50)
        print(f"ID: {moeda[0]}")
        print(f"Nome: {moeda[1]}")
        print(f"Símbolo: {moeda[2].upper()}")
        print(f"Preço: {self.formatar_valor(moeda[3], 'preco')}")
        print(f"Variação 24h: {self.formatar_valor(moeda[4], 'variacao')}")
        print(f"Market Cap: {self.formatar_valor(moeda[5], 'market_cap')}")
        print(f"Última atualização: {moeda[6] if moeda[6] else 'N/A'}")
        print("="*50)
    
    def executar_busca(self):
        if not self.conectar_banco():
            print("Falha ao conectar com o banco de dados.")
            return
        
        print("BUSCADOR DE CRIPTOMOEDAS")
        print("Digite 'sair' para encerrar\n")
        
        while True:
            print("\nOpções de busca:")
            print("1. Buscar por ID")
            print("2. Buscar por Nome")
            print("3. Sair")
            
            opcao = input("\nEscolha uma opção (1-3): ").strip()
            
            if opcao == "3" or opcao.lower() == "sair":
                break
            
            if opcao not in ["1", "2"]:
                print("Opção inválida.")
                continue
            
            tipo_busca = "id" if opcao == "1" else "nome"
            termo = input(f"Digite o {tipo_busca}: ").strip()
            
            if termo.lower() == "sair":
                break
            
            if not termo:
                print("Termo de busca não pode estar vazio.")
                continue
            
            resultados = self.buscar_moedas(tipo_busca, termo)
            
            if not resultados:
                print("Nenhuma moeda encontrada.")
                continue
            
            print(f"\n{len(resultados)} resultado(s) encontrado(s):")
            print("-" * 60)
            
            for i, moeda in enumerate(resultados[:10], 1):  # Limita a 10 resultados
                market_cap_str = self.formatar_valor(moeda[5], 'market_cap')
                print(f"{i:2d}. {moeda[1]} ({moeda[2].upper()}) - Market Cap: {market_cap_str}")
            
            if len(resultados) > 10:
                print(f"... e mais {len(resultados) - 10} resultado(s)")
            
            try:
                escolha = input("\nNúmero da moeda para ver detalhes (ou Enter para nova busca): ").strip()
                
                if not escolha:
                    continue
                
                num_escolha = int(escolha)
                if 1 <= num_escolha <= min(len(resultados), 10):
                    self.exibir_detalhes_moeda(resultados[num_escolha - 1])
                else:
                    print("Número inválido.")
                    
            except ValueError:
                print("Entrada inválida.")
        
        self.fechar_conexao()
        print("\nBusca finalizada.")

if __name__ == "__main__":
    buscador = BuscadorCriptomoedas()
    buscador.executar_busca()
