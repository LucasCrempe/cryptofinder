import sqlite3
import pickle
from typing import List, Tuple, Set, Optional
from pathlib import Path

class CryptocurrencySearchEngine:
    
    def __init__(self, db_path: str = "data/criptomoedas.db", index_path: str = "data/indice_invertido.pkl"):
        self.db_path = db_path
        self.index_path = index_path
        self.connection = None
        self.inverted_index = {}
        self.index_loaded = self._load_inverted_index()
        
    def _load_inverted_index(self) -> bool:
        try:
            with open(self.index_path, "rb") as file:
                self.inverted_index = pickle.load(file)
            return True
        except FileNotFoundError:
            print("Warning: Inverted index not found. Using traditional search.")
            return False
        except Exception as error:
            print(f"Error loading inverted index: {error}")
            return False
    
    def _connect_database(self) -> bool:
        try:
            self.connection = sqlite3.connect(self.db_path)
            return True
        except sqlite3.Error as error:
            print(f"Database connection error: {error}")
            return False
    
    def _close_connection(self):
        if self.connection:
            self.connection.close()
    
    def _search_ids_by_term(self, term: str) -> Set[str]:
        if not self.inverted_index:
            return set()
        
        normalized_term = term.lower().strip()
        found_ids = set()
        
        if normalized_term in self.inverted_index:
            found_ids.update(self.inverted_index[normalized_term])
        
        for indexed_term, ids in self.inverted_index.items():
            if normalized_term in indexed_term:
                found_ids.update(ids)
        
        return found_ids
    
    def _search_with_index(self, term: str) -> List[Tuple]:
        """Busca usando índice invertido."""
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
    
    def _search_traditional(self, field: str, term: str) -> List[Tuple]:
        if not self.connection and not self._connect_database():
            return []
        
        cursor = self.connection.cursor()
        query = f"SELECT * FROM moedas WHERE LOWER({field}) LIKE ? ORDER BY market_cap DESC"
        
        try:
            cursor.execute(query, (f"%{term.lower()}%",))
            return cursor.fetchall()
        except sqlite3.Error:
            return []
    
    def search_by_field(self, field: str, term: str) -> List[Tuple]:
        # Se temos índice invertido, usar para busca otimizada
        if self.index_loaded:
            return self._search_with_index(term)
        else:
            # Fallback para busca tradicional
            return self._search_traditional(field, term)
    
    def format_currency_value(self, value, value_type: str) -> str:
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
        if not self._connect_database():
            print("Failed to connect to database.")
            return
        
        print("CRYPTOCURRENCY SEARCH ENGINE")
        print("=" * 50)
        
        if self.index_loaded:
            print("Search optimization: Inverted index enabled")
        else:
            print("Search optimization: Traditional mode")
        
        print("Type 'exit' to quit\n")
        
        while True:
            print("\nSearch Options:")
            print("1. Search by ID")
            print("2. Search by Name")
            print("3. Search by Symbol")
            print("4. Exit")
            
            try:
                option = input("\nSelect option (1-4): ").strip()
                
                if option == "4" or option.lower() == "exit":
                    break
                
                field_map = {"1": "id", "2": "nome", "3": "simbolo"}
                field = field_map.get(option)
                
                if not field:
                    print("Invalid option.")
                    continue
                
                field_display = "symbol" if field == "simbolo" else field
                term = input(f"Enter {field_display}: ").strip()
                
                if term.lower() == "exit":
                    break
                if not term:
                    print("Search term cannot be empty.")
                    continue
                
                print(f"\nSearching for '{term}' by {field_display}...")
                results = self.search_by_field(field, term)
                
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
    search_engine = CryptocurrencySearchEngine()
    search_engine.run_search_interface()

if __name__ == "__main__":
    main()
