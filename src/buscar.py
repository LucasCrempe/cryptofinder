import sqlite3
import pickle
from typing import List, Tuple, Set, Optional
from pathlib import Path

class CryptocurrencySearchEngine:
    """
    Sistema de busca de criptomoedas com suporte a índice invertido.
    Permite busca otimizada por termos ou busca tradicional por campos específicos.
    """
    
    def __init__(self, db_path: str = "data/criptomoedas.db", index_path: str = "data/indice_invertido.pkl"):
        self.db_path = db_path
        self.index_path = index_path
        self.connection = None
        self.inverted_index = {}
        self.index_loaded = self._load_inverted_index()
        
    def _load_inverted_index(self) -> bool:
        """Carrega o índice invertido do arquivo pickle."""
        try:
            with open(self.index_path, "rb") as file:
                self.inverted_index = pickle.load(file)
            return True
        except FileNotFoundError:
            print("Warning: Inverted index not found. Run 'python indiceinvertido.py' first.")
            print("System will operate in traditional search mode.")
            return False
        except Exception as error:
            print(f"Error loading inverted index: {error}")
            return False
    
    def _connect_database(self) -> bool:
        """Estabelece conexão com o banco de dados."""
        try:
            self.connection = sqlite3.connect(self.db_path)
            return True
        except sqlite3.Error as error:
            print(f"Database connection error: {error}")
            return False
    
    def _close_connection(self):
        """Fecha a conexão com o banco de dados."""
        if self.connection:
            self.connection.close()
    
    def _search_ids_by_term(self, term: str) -> Set[str]:
        """Busca IDs de criptomoedas usando o índice invertido."""
        if not self.inverted_index:
            return set()
        
        normalized_term = term.lower().strip()
        found_ids = set()
        
        # Busca exata
        if normalized_term in self.inverted_index:
            found_ids.update(self.inverted_index[normalized_term])
        
        # Busca parcial
        for indexed_term, ids in self.inverted_index.items():
            if normalized_term in indexed_term or indexed_term in normalized_term:
                found_ids.update(ids)
        
        return found_ids
    
    def search_with_index(self, term: str) -> List[Tuple]:
        """Executa busca usando índice invertido."""
        found_ids = self._search_ids_by_term(term)
        
        if not found_ids:
            return []
        
        if not self.connection and not self._connect_database():
            return []
        
        cursor = self.connection.cursor()
        placeholders = ','.join(['?' for _ in found_ids])
        query = f"""
            SELECT * FROM moedas 
            WHERE id IN ({placeholders}) 
            ORDER BY market_cap DESC NULLS LAST
        """
        
        try:
            cursor.execute(query, list(found_ids))
            return cursor.fetchall()
        except sqlite3.Error as error:
            print(f"Database query error: {error}")
            return []
    
    def search_traditional(self, field: str, term: str) -> List[Tuple]:
        """Executa busca tradicional por campo específico."""
        if not self.connection and not self._connect_database():
            return []
        
        cursor = self.connection.cursor()
        
        if field not in ["id", "nome"]:
            return []
        
        query = f"SELECT * FROM moedas WHERE LOWER({field}) LIKE ? ORDER BY market_cap DESC"
        
        try:
            cursor.execute(query, (f"%{term.lower()}%",))
            return cursor.fetchall()
        except sqlite3.Error:
            return []
    
    def format_currency_value(self, value, value_type: str) -> str:
        """Formata valores monetários para exibição."""
        if value is None:
            return "N/A"
        
        try:
            if value_type == "price":
                return f"${value:.8f}" if value < 0.01 else f"${value:,.2f}"
            elif value_type == "change":
                return f"{value:+.2f}%"
            elif value_type == "market_cap":
                if value >= 1e9:
                    return f"${value/1e9:.2f}B"
                elif value >= 1e6:
                    return f"${value/1e6:.2f}M"
                else:
                    return f"${value:,.0f}"
        except (ValueError, TypeError):
            return "N/A"
        
        return str(value)
    
    def display_cryptocurrency_details(self, crypto_data: Tuple):
        """Exibe detalhes completos de uma criptomoeda."""
        separator = "=" * 60
        print(f"\n{separator}")
        print("CRYPTOCURRENCY DETAILS")
        print(separator)
        print(f"ID: {crypto_data[0]}")
        print(f"Name: {crypto_data[1]}")
        print(f"Symbol: {crypto_data[2].upper()}")
        print(f"Price: {self.format_currency_value(crypto_data[3], 'price')}")
        print(f"24h Change: {self.format_currency_value(crypto_data[4], 'change')}")
        print(f"Market Cap: {self.format_currency_value(crypto_data[5], 'market_cap')}")
        print(f"Last Updated: {crypto_data[6] if crypto_data[6] else 'N/A'}")
        print(separator)
    
    def display_search_results(self, results: List[Tuple], max_display: int = 15):
        """Exibe lista de resultados da busca."""
        if not results:
            print("No cryptocurrencies found.")
            return None
        
        print(f"\n{len(results)} result(s) found:")
        print("-" * 70)
        
        display_count = min(len(results), max_display)
        for i, crypto in enumerate(results[:display_count], 1):
            market_cap = self.format_currency_value(crypto[5], 'market_cap')
            price = self.format_currency_value(crypto[3], 'price')
            print(f"{i:2d}. {crypto[1]} ({crypto[2].upper()}) - {price} - MC: {market_cap}")
        
        if len(results) > max_display:
            print(f"... and {len(results) - max_display} more result(s)")
        
        return self._get_user_selection(results, display_count)
    
    def _get_user_selection(self, results: List[Tuple], display_count: int) -> Optional[Tuple]:
        """Obtém seleção do usuário para ver detalhes."""
        try:
            selection = input("\nEnter number to view details (Enter for new search): ").strip()
            
            if not selection:
                return None
            
            selection_num = int(selection)
            if 1 <= selection_num <= display_count:
                return results[selection_num - 1]
            else:
                print("Invalid number.")
                return None
                
        except ValueError:
            print("Invalid input.")
            return None
    
    def run_search_interface(self):
        """Interface principal do sistema de busca."""
        if not self._connect_database():
            print("Failed to connect to database.")
            return
        
        print("CRYPTOCURRENCY SEARCH ENGINE")
        print("=" * 50)
        
        if self.index_loaded:
            print(f"Inverted index loaded: {len(self.inverted_index)} unique terms")
        else:
            print("Operating in traditional search mode")
        
        print("Type 'exit' to quit\n")
        
        while True:
            print("\nSearch Options:")
            
            if self.index_loaded:
                print("1. Smart Search (uses inverted index)")
                print("2. Search by ID")
                print("3. Search by Name")
                print("4. Exit")
                max_option = 4
            else:
                print("1. Search by ID")
                print("2. Search by Name")
                print("3. Exit")
                max_option = 3
            
            try:
                option = input(f"\nSelect option (1-{max_option}): ").strip()
                
                if option == str(max_option) or option.lower() == "exit":
                    break
                
                if option not in [str(i) for i in range(1, max_option + 1)]:
                    print("Invalid option.")
                    continue
                
                # Smart search with inverted index
                if option == "1" and self.index_loaded:
                    term = input("Enter search term: ").strip()
                    if term.lower() == "exit":
                        break
                    if not term:
                        print("Search term cannot be empty.")
                        continue
                    
                    print(f"\nSearching for '{term}' using inverted index...")
                    results = self.search_with_index(term)
                
                # Traditional search
                else:
                    if self.index_loaded:
                        field = "id" if option == "2" else "nome"
                    else:
                        field = "id" if option == "1" else "nome"
                    
                    term = input(f"Enter {field}: ").strip()
                    if term.lower() == "exit":
                        break
                    if not term:
                        print("Search term cannot be empty.")
                        continue
                    
                    print(f"\nSearching for '{term}' by {field}...")
                    results = self.search_traditional(field, term)
                
                # Display results and handle selection
                selected_crypto = self.display_search_results(results)
                if selected_crypto:
                    self.display_cryptocurrency_details(selected_crypto)
                
            except KeyboardInterrupt:
                print("\n\nSearch interrupted by user.")
                break
            except Exception as error:
                print(f"Unexpected error: {error}")
        
        self._close_connection()
        print("\nSearch session ended.")

def main():
    """Função principal."""
    search_engine = CryptocurrencySearchEngine()
    search_engine.run_search_interface()

if __name__ == "__main__":
    main()
