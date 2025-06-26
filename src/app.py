from reactpy import component, html, hooks, run
from reactpy.backend.fastapi import configure
from fastapi import FastAPI
import sqlite3
import pickle
from typing import List, Tuple, Set

class CryptoSearchEngine:
    def __init__(self, db_path: str = "data/criptomoedas.db", index_path: str = "data/indice_invertido.pkl"):
        self.db_path = db_path
        self.index_path = index_path
        self.inverted_index = {}
        self.index_loaded = self._load_inverted_index()
        
    def _load_inverted_index(self) -> bool:
        try:
            with open(self.index_path, "rb") as file:
                self.inverted_index = pickle.load(file)
            return True
        except Exception as e:
            print(f"Error loading inverted index: {e}")
            return False
    
    def _search_ids_by_term(self, term: str) -> Set[str]:
        if not self.inverted_index:
            return set()
        
        normalized_term = term.lower().strip()
        found_ids = set()
        
        # Busca exata primeiro
        if normalized_term in self.inverted_index:
            found_ids.update(self.inverted_index[normalized_term])
        
        # Busca parcial apenas se não encontrou resultado exato
        if not found_ids:
            for indexed_term, ids in self.inverted_index.items():
                if normalized_term in indexed_term:
                    found_ids.update(ids)
        
        return found_ids
    
    def search_by_id(self, term: str) -> List[Tuple]:
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            query = "SELECT * FROM moedas WHERE LOWER(id) LIKE ? ORDER BY market_cap DESC LIMIT 50"
            cursor.execute(query, (f"%{term.lower()}%",))
            results = cursor.fetchall()
            conn.close()
            return results
        except Exception as e:
            print(f"Error in ID search: {e}")
            return []
    
    def search_by_name(self, term: str) -> List[Tuple]:
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            query = "SELECT * FROM moedas WHERE LOWER(nome) LIKE ? ORDER BY market_cap DESC LIMIT 50"
            cursor.execute(query, (f"%{term.lower()}%",))
            results = cursor.fetchall()
            conn.close()
            return results
        except Exception as e:
            print(f"Error in name search: {e}")
            return []
    
    def search_by_symbol(self, term: str) -> List[Tuple]:
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            query = "SELECT * FROM moedas WHERE LOWER(simbolo) LIKE ? ORDER BY market_cap DESC LIMIT 50"
            cursor.execute(query, (f"%{term.lower()}%",))
            results = cursor.fetchall()
            conn.close()
            return results
        except Exception as e:
            print(f"Error in symbol search: {e}")
            return []
    
    def search_with_inverted_index(self, term: str) -> List[Tuple]:
        if not self.index_loaded:
            print("Inverted index not loaded, using name search as fallback")
            return self.search_by_name(term)
        
        found_ids = self._search_ids_by_term(term)
        if not found_ids:
            return []
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            placeholders = ','.join(['?' for _ in found_ids])
            query = f"SELECT * FROM moedas WHERE id IN ({placeholders}) ORDER BY market_cap DESC"
            cursor.execute(query, list(found_ids))
            results = cursor.fetchall()
            conn.close()
            return results
        except Exception as e:
            print(f"Error in inverted index search: {e}")
            return []

search_engine = CryptoSearchEngine()

@component
def Header():
    return html.header(
        {
            "style": {
                "background": "rgba(255, 255, 255, 0.1)",
                "backdrop-filter": "blur(20px)",
                "padding": "1rem 2rem",
                "display": "flex",
                "justify-content": "space-between",
                "align-items": "center",
                "border-bottom": "1px solid rgba(255, 255, 255, 0.1)"
            }
        },
        html.div(
            {
                "style": {
                    "display": "flex",
                    "align-items": "center",
                    "gap": "0.5rem"
                }
            },
            html.div(
                {
                    "style": {
                        "width": "32px",
                        "height": "32px",
                        "background": "linear-gradient(45deg, #00d4ff, #0099cc)",
                        "border-radius": "8px",
                        "display": "flex",
                        "align-items": "center",
                        "justify-content": "center",
                        "font-weight": "bold",
                        "color": "white",
                        "font-size": "18px"
                    }
                },
                "₿"
            ),
            html.h1(
                {
                    "style": {
                        "color": "white",
                        "font-size": "1.8rem",
                        "font-weight": "700",
                        "margin": "0",
                        "font-family": "'Inter', sans-serif"
                    }
                },
                "CryptoFinder"
            )
        ),
        html.nav(
            {
                "style": {
                    "display": "flex",
                    "gap": "2rem",
                    "align-items": "center"
                }
            },
            html.a(
                {
                    "style": {
                        "color": "rgba(255, 255, 255, 0.9)",
                        "text-decoration": "none",
                        "font-weight": "500",
                        "font-family": "'Inter', sans-serif",
                        "cursor": "pointer"
                    }
                },
                "Home"
            ),
            html.a(
                {
                    "style": {
                        "color": "rgba(255, 255, 255, 0.7)",
                        "text-decoration": "none",
                        "font-weight": "500",
                        "font-family": "'Inter', sans-serif",
                        "cursor": "pointer"
                    }
                },
                "About"
            )
        )
    )

@component
def SearchTypeButton(value, label, is_active, on_click):
    return html.button(
        {
            "on_click": lambda _: on_click(),
            "style": {
                "padding": "0.8rem 1.5rem",
                "border": "2px solid" + (" #667eea" if is_active else " #e2e8f0"),
                "border-radius": "12px",
                "background": "#667eea" if is_active else "white",
                "color": "white" if is_active else "#64748b",
                "cursor": "pointer",
                "font-weight": "600" if is_active else "500",
                "font-family": "'Inter', sans-serif",
                "transition": "all 0.3s ease",
                "font-size": "0.9rem"
            }
        },
        label
    )

def get_placeholder(search_type):
    placeholders = {
        "inverted_index": "Search anything... (Bitcoin, BTC, ethereum)",
        "id": "Enter cryptocurrency ID (bitcoin, ethereum)",
        "name": "Enter cryptocurrency name (Bitcoin, Ethereum)",
        "symbol": "Enter symbol (BTC, ETH, ADA)"
    }
    return placeholders.get(search_type, "Search cryptocurrencies...")

def get_search_type_label(search_type):
    labels = {
        "inverted_index": "Smart Search",
        "id": "ID Search",
        "name": "Name Search",
        "symbol": "Symbol Search"
    }
    return labels.get(search_type, "Search")

def format_price(value):
    if value is None:
        return "N/A"
    try:
        if value < 0.01:
            return f"${value:.8f}"
        else:
            return f"${value:,.2f}"
    except:
        return "N/A"

def format_change(value):
    if value is None:
        return "N/A"
    try:
        return f"{value:+.2f}%"
    except:
        return "N/A"

def format_market_cap(value):
    if value is None:
        return "N/A"
    try:
        if value >= 1e9:
            return f"${value/1e9:.2f}B"
        elif value >= 1e6:
            return f"${value/1e6:.2f}M"
        else:
            return f"${value:,.0f}"
    except:
        return "N/A"

def format_date(date_str):
    if not date_str:
        return "N/A"
    try:
        return date_str[:19].replace('T', ' ')
    except:
        return "N/A"

@component
def SearchInterface():
    search_term, set_search_term = hooks.use_state("")
    search_type, set_search_type = hooks.use_state("inverted_index")
    results, set_results = hooks.use_state([])
    loading, set_loading = hooks.use_state(False)
    show_about, set_show_about = hooks.use_state(False)
    search_performed, set_search_performed = hooks.use_state(False)
    
    def handle_search():
        if not search_term.strip():
            set_results([])
            set_search_performed(False)
            return
        
        set_loading(True)
        set_search_performed(True)
        
        try:
            if search_type == "id":
                search_results = search_engine.search_by_id(search_term)
            elif search_type == "name":
                search_results = search_engine.search_by_name(search_term)
            elif search_type == "symbol":
                search_results = search_engine.search_by_symbol(search_term)
            else:  # inverted_index
                search_results = search_engine.search_with_inverted_index(search_term)
            
            set_results(search_results)
        except Exception as e:
            print(f"Search error: {e}")
            set_results([])
        finally:
            set_loading(False)
    
    def handle_input_change(event):
        value = event["target"]["value"]
        set_search_term(value)
        if not value.strip():
            set_results([])
            set_search_performed(False)
    
    if show_about:
        return AboutPage(lambda: set_show_about(False))
    
    # Definir os tipos de busca e labels
    search_types = ["inverted_index", "id", "name", "symbol"]
    search_labels = {
        "inverted_index": "Smart Search",
        "id": "Search by ID", 
        "name": "Search by Name",
        "symbol": "Search by Symbol"
    }
    
    return html.div(
        {
            "style": {
                "min-height": "100vh",
                "background": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                "font-family": "'Inter', -apple-system, BlinkMacSystemFont, sans-serif"
            }
        },
        # Google Fonts Import
        html.link({
            "href": "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap",
            "rel": "stylesheet"
        }),
        
        Header(),
        
        # Main Content
        html.main(
            {
                "style": {
                    "padding": "4rem 2rem",
                    "max-width": "1200px",
                    "margin": "0 auto"
                }
            },
            
            # Hero Section
            html.div(
                {
                    "style": {
                        "text-align": "center",
                        "margin-bottom": "4rem"
                    }
                },
                html.h2(
                    {
                        "style": {
                            "color": "white",
                            "font-size": "3.5rem",
                            "font-weight": "700",
                            "margin": "0 0 1rem 0",
                            "text-shadow": "0 4px 20px rgba(0,0,0,0.3)",
                            "line-height": "1.1"
                        }
                    },
                    "Find Any Cryptocurrency"
                ),
                html.p(
                    {
                        "style": {
                            "color": "rgba(255, 255, 255, 0.8)",
                            "font-size": "1.3rem",
                            "margin": "0",
                            "font-weight": "300",
                            "max-width": "600px",
                            "margin": "0 auto"
                        }
                    },
                    "Advanced search engine with real-time data and intelligent filtering"
                )
            ),
            
            # Search Container
            html.div(
                {
                    "style": {
                        "background": "rgba(255, 255, 255, 0.95)",
                        "backdrop-filter": "blur(20px)",
                        "border-radius": "24px",
                        "box-shadow": "0 20px 60px rgba(0,0,0,0.1)",
                        "overflow": "hidden",
                        "border": "1px solid rgba(255, 255, 255, 0.2)"
                    }
                },
                
                # Search Controls
                html.div(
                    {
                        "style": {
                            "padding": "2.5rem",
                            "border-bottom": "1px solid rgba(0,0,0,0.05)" if results or (search_performed and not loading) else "none"
                        }
                    },
                    
                    # Search Type Selector
                    html.div(
                        {
                            "style": {
                                "display": "flex",
                                "gap": "1rem",
                                "margin-bottom": "2rem",
                                "flex-wrap": "wrap",
                                "justify-content": "center"
                            }
                        },
                        *[SearchTypeButton(
                            search_type_option,
                            search_labels[search_type_option],
                            search_type == search_type_option,
                            lambda option=search_type_option: set_search_type(option)
                        ) for search_type_option in search_types]
                    ),
                    
                    # Search Input
                    html.div(
                        {
                            "style": {
                                "position": "relative",
                                "max-width": "600px",
                                "margin": "0 auto"
                            }
                        },
                        html.input({
                            "type": "text",
                            "placeholder": get_placeholder(search_type),
                            "value": search_term,
                            "on_input": handle_input_change,
                            "on_key_down": lambda event: handle_search() if event["key"] == "Enter" else None,
                            "style": {
                                "width": "calc(100% - 120px)",  # Ajustado para dar espaço ao botão
                                "padding": "1.2rem 1.5rem 1.2rem 3.5rem",
                                "font-size": "1.1rem",
                                "border": "2px solid #e2e8f0",
                                "border-radius": "16px",
                                "outline": "none",
                                "transition": "all 0.3s ease",
                                "background": "#ffffff",
                                "font-family": "'Inter', sans-serif",
                                "box-shadow": "0 4px 12px rgba(0,0,0,0.05)"
                            }
                        }),
                        html.div(
                            {
                                "style": {
                                    "position": "absolute",
                                    "left": "1.2rem",
                                    "top": "50%",
                                    "transform": "translateY(-50%)",
                                    "color": "#64748b",
                                    "font-size": "1.2rem"
                                }
                            },
                            "🔍"
                        ),
                        html.button(
                            {
                                "on_click": lambda _: handle_search(),
                                "disabled": loading,
                                "style": {
                                    "position": "absolute",
                                    "right": "8px",
                                    "top": "50%",
                                    "transform": "translateY(-50%)",
                                    "background": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                                    "color": "white",
                                    "border": "none",
                                    "border-radius": "12px",
                                    "padding": "0.8rem 1.5rem",
                                    "cursor": "pointer" if not loading else "not-allowed",
                                    "font-weight": "600",
                                    "font-family": "'Inter', sans-serif",
                                    "transition": "all 0.3s ease",
                                    "opacity": "0.8" if loading else "1",
                                    "width": "100px"  # Largura fixa para o botão
                                }
                            },
                            "⏳" if loading else "Search"
                        )
                    )
                ),
                
                # Results
                ResultsSection(results, loading, search_type, search_performed, search_term)
            ),
            
            # About Button
            html.div(
                {
                    "style": {
                        "text-align": "center",
                        "margin-top": "3rem"
                    }
                },
                html.button(
                    {
                        "on_click": lambda _: set_show_about(True),
                        "style": {
                            "background": "rgba(255, 255, 255, 0.1)",
                            "color": "white",
                            "border": "1px solid rgba(255, 255, 255, 0.2)",
                            "padding": "0.8rem 2rem",
                            "border-radius": "12px",
                            "cursor": "pointer",
                            "font-family": "'Inter', sans-serif",
                            "font-weight": "500",
                            "backdrop-filter": "blur(10px)",
                            "transition": "all 0.3s ease"
                        }
                    },
                    "About Us"
                )
            )
        )
    )

@component
def ResultsSection(results, loading, search_type, search_performed, search_term):
    if loading:
        return html.div(
            {
                "style": {
                    "padding": "4rem",
                    "text-align": "center"
                }
            },
            html.div(
                {
                    "style": {
                        "display": "inline-block",
                        "width": "40px",
                        "height": "40px",
                        "border": "4px solid #f3f3f3",
                        "border-top": "4px solid #667eea",
                        "border-radius": "50%",
                        "animation": "spin 1s linear infinite"
                    }
                }
            ),
            html.p(
                {
                    "style": {
                        "margin-top": "1.5rem",
                        "color": "#64748b",
                        "font-size": "1.1rem",
                        "font-family": "'Inter', sans-serif"
                    }
                },
                f"Searching with {get_search_type_label(search_type)}..."
            ),
            html.style("""
                @keyframes spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }
            """)
        )
    
    # Show "No results found" message if search was performed but no results
    if search_performed and not results and not loading:
        return html.div(
            {
                "style": {
                    "padding": "4rem",
                    "text-align": "center"
                }
            },
            html.div(
                {
                    "style": {
                        "font-size": "4rem",
                        "margin-bottom": "1.5rem",
                        "opacity": "0.5"
                    }
                },
                "🔍"
            ),
            html.h3(
                {
                    "style": {
                        "color": "#1e293b",
                        "font-size": "1.5rem",
                        "font-weight": "600",
                        "margin-bottom": "1rem",
                        "font-family": "'Inter', sans-serif"
                    }
                },
                "No Results Found"
            ),
            html.p(
                {
                    "style": {
                        "color": "#64748b",
                        "font-size": "1.1rem",
                        "margin-bottom": "1.5rem",
                        "font-family": "'Inter', sans-serif",
                        "max-width": "500px",
                        "margin": "0 auto 1.5rem auto",
                        "line-height": "1.6"
                    }
                },
                f"We couldn't find any cryptocurrencies matching \"{search_term}\" using {get_search_type_label(search_type).lower()}."
            ),
            html.div(
                {
                    "style": {
                        "background": "#f8fafc",
                        "border": "1px solid #e2e8f0",
                        "border-radius": "12px",
                        "padding": "1.5rem",
                        "max-width": "400px",
                        "margin": "0 auto"
                    }
                },
                html.h4(
                    {
                        "style": {
                            "color": "#1e293b",
                            "font-size": "1rem",
                            "font-weight": "600",
                            "margin-bottom": "0.8rem",
                            "font-family": "'Inter', sans-serif"
                        }
                    },
                    "Try these suggestions:"
                ),
                html.ul(
                    {
                        "style": {
                            "color": "#64748b",
                            "font-size": "0.9rem",
                            "margin": "0",
                            "padding-left": "1.2rem",
                            "font-family": "'Inter', sans-serif",
                            "line-height": "1.6"
                        }
                    },
                    html.li("Check your spelling"),
                    html.li("Try different search terms"),
                    html.li("Use a different search type"),
                    html.li("Try searching for popular coins like Bitcoin or Ethereum")
                )
            )
        )
    
    if not results:
        return html.div()
    
    return html.div(
        {
            "style": {
                "max-height": "600px",
                "overflow-y": "auto"
            }
        },
        html.div(
            {
                "style": {
                    "padding": "1.5rem 2.5rem",
                    "background": "#f8fafc",
                    "border-bottom": "1px solid #e2e8f0",
                    "display": "flex",
                    "justify-content": "space-between",
                    "align-items": "center"
                }
            },
            html.h3(
                {
                    "style": {
                        "margin": "0",
                        "color": "#1e293b",
                        "font-size": "1.2rem",
                        "font-weight": "600",
                        "font-family": "'Inter', sans-serif"
                    }
                },
                f"{len(results)} result{'s' if len(results) != 1 else ''} found"
            ),
            html.span(
                {
                    "style": {
                        "color": "#64748b",
                        "font-size": "0.9rem",
                        "font-family": "'Inter', sans-serif"
                    }
                },
                f"Using {get_search_type_label(search_type)}"
            )
        ),
        *[CryptoCard(crypto) for crypto in results[:50]]
    )

@component
def CryptoCard(crypto):
    # crypto = (id, nome, simbolo, preco_usd, variacao_24h, market_cap, ultima_atualizacao)
    nome = crypto[1] or "N/A"
    simbolo = (crypto[2] or "").upper()
    crypto_id = crypto[0] or "N/A"
    preco = format_price(crypto[3])
    variacao = format_change(crypto[4])
    market_cap = format_market_cap(crypto[5])
    ultima_atualizacao = format_date(crypto[6])
    
    change_color = "#10b981" if crypto[4] and crypto[4] > 0 else "#ef4444" if crypto[4] and crypto[4] < 0 else "#64748b"
    
    return html.div(
        {
            "style": {
                "padding": "2rem 2.5rem",
                "border-bottom": "1px solid #f1f5f9",
                "transition": "all 0.2s ease",
                "cursor": "pointer"
            }
        },
        html.div(
            {
                "style": {
                    "display": "grid",
                    "grid-template-columns": "1fr auto",
                    "gap": "2rem",
                    "align-items": "center"
                }
            },
            
            # Left side - Main info
            html.div(
                html.div(
                    {
                        "style": {
                            "display": "flex",
                            "align-items": "center",
                            "gap": "1rem",
                            "margin-bottom": "0.8rem"
                        }
                    },
                    html.div(
                        {
                            "style": {
                                "width": "40px",
                                "height": "40px",
                                "background": "linear-gradient(45deg, #667eea, #764ba2)",
                                "border-radius": "12px",
                                "display": "flex",
                                "align-items": "center",
                                "justify-content": "center",
                                "color": "white",
                                "font-weight": "bold",
                                "font-size": "1.2rem"
                            }
                        },
                        simbolo[:2] if simbolo else "?"
                    ),
                    html.div(
                        html.h4(
                            {
                                "style": {
                                    "margin": "0 0 0.2rem 0",
                                    "font-size": "1.3rem",
                                    "font-weight": "600",
                                    "color": "#1e293b",
                                    "font-family": "'Inter', sans-serif"
                                }
                            },
                            nome
                        ),
                        html.div(
                            {
                                "style": {
                                    "display": "flex",
                                    "gap": "1rem",
                                    "align-items": "center"
                                }
                            },
                            html.span(
                                {
                                    "style": {
                                        "background": "#e2e8f0",
                                        "color": "#475569",
                                        "padding": "0.3rem 0.8rem",
                                        "border-radius": "8px",
                                        "font-size": "0.8rem",
                                        "font-weight": "600",
                                        "font-family": "'Inter', sans-serif"
                                    }
                                },
                                simbolo
                            ),
                            html.span(
                                {
                                    "style": {
                                        "color": "#64748b",
                                        "font-size": "0.9rem",
                                        "font-family": "'Inter', sans-serif"
                                    }
                                },
                                f"ID: {crypto_id}"
                            )
                        )
                    )
                ),
                
                # Additional info
                html.div(
                    {
                        "style": {
                            "display": "grid",
                            "grid-template-columns": "repeat(auto-fit, minmax(200px, 1fr))",
                            "gap": "1rem",
                            "margin-top": "1rem"
                        }
                    },
                    html.div(
                        html.span(
                            {
                                "style": {
                                    "color": "#64748b",
                                    "font-size": "0.8rem",
                                    "text-transform": "uppercase",
                                    "letter-spacing": "0.05em",
                                    "font-weight": "500"
                                }
                            },
                            "Market Cap"
                        ),
                        html.div(
                            {
                                "style": {
                                    "color": "#1e293b",
                                    "font-weight": "600",
                                    "font-size": "1rem",
                                    "margin-top": "0.2rem"
                                }
                            },
                            market_cap
                        )
                    ),
                    html.div(
                        html.span(
                            {
                                "style": {
                                    "color": "#64748b",
                                    "font-size": "0.8rem",
                                    "text-transform": "uppercase",
                                    "letter-spacing": "0.05em",
                                    "font-weight": "500"
                                }
                            },
                            "Last Updated"
                        ),
                        html.div(
                            {
                                "style": {
                                    "color": "#1e293b",
                                    "font-weight": "500",
                                    "font-size": "0.9rem",
                                    "margin-top": "0.2rem"
                                }
                            },
                            ultima_atualizacao
                        )
                    )
                )
            ),
            
            # Right side - Price info
            html.div(
                {
                    "style": {
                        "text-align": "right"
                    }
                },
                html.div(
                    {
                        "style": {
                            "font-size": "2rem",
                            "font-weight": "700",
                            "color": "#1e293b",
                            "margin-bottom": "0.5rem",
                            "font-family": "'Inter', sans-serif"
                        }
                    },
                    preco
                ),
                html.div(
                    {
                        "style": {
                            "font-size": "1.1rem",
                            "font-weight": "600",
                            "color": change_color,
                            "display": "flex",
                            "align-items": "center",
                            "justify-content": "flex-end",
                            "gap": "0.5rem"
                        }
                    },
                    html.span("📈" if crypto[4] and crypto[4] > 0 else "📉" if crypto[4] and crypto[4] < 0 else "➡️"),
                    variacao
                )
            )
        )
    )

@component
def AboutPage(on_back):
    return html.div(
        {
            "style": {
                "min-height": "100vh",
                "background": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                "font-family": "'Inter', sans-serif",
                "padding": "2rem"
            }
        },
        html.div(
            {
                "style": {
                    "max-width": "800px",
                    "margin": "0 auto",
                    "background": "rgba(255, 255, 255, 0.95)",
                    "border-radius": "24px",
                    "padding": "3rem",
                    "backdrop-filter": "blur(20px)"
                }
            },
            html.button(
                {
                    "on_click": lambda _: on_back(),
                    "style": {
                        "background": "none",
                        "border": "none",
                        "color": "#667eea",
                        "font-size": "1rem",
                        "cursor": "pointer",
                        "margin-bottom": "2rem",
                        "padding": "0.5rem 0",
                        "font-weight": "500",
                        "display": "flex",
                        "align-items": "center",
                        "gap": "0.5rem"
                    }
                },
                "← Back to Search"
            ),
            html.h1(
                {
                    "style": {
                        "color": "#1e293b",
                        "font-size": "2.5rem",
                        "font-weight": "700",
                        "margin-bottom": "2rem",
                        "text-align": "center"
                    }
                },
                "About CryptoFinder"
            ),
            html.div(
                {
                    "style": {
                        "color": "#475569",
                        "font-size": "1.2rem",
                        "line-height": "1.8",
                        "text-align": "center",
                        "max-width": "600px",
                        "margin": "0 auto 3rem auto"
                    }
                },
                "Cryptocurrency search engine using inverted indexes for efficient data retrieval. Collects real-time crypto data from CoinGecko API and organizes it with Python."
            ),
            html.div(
                {
                    "style": {
                        "display": "grid",
                        "grid-template-columns": "repeat(auto-fit, minmax(250px, 1fr))",
                        "gap": "2rem",
                        "margin-top": "3rem"
                    }
                },
                FeatureCard("🔍", "Smart Search", "Advanced inverted index for lightning-fast searches"),
                FeatureCard("📊", "Real-time Data", "Live cryptocurrency data from CoinGecko API"),
                FeatureCard("🐍", "Python Powered", "Built with modern Python and ReactPy"),
                FeatureCard("⚡", "High Performance", "Optimized for speed and efficiency")
            )
        )
    )

@component
def FeatureCard(icon, title, description):
    return html.div(
        {
            "style": {
                "text-align": "center",
                "padding": "2rem",
                "background": "#f8fafc",
                "border-radius": "16px",
                "border": "1px solid #e2e8f0"
            }
        },
        html.div(
            {
                "style": {
                    "font-size": "2.5rem",
                    "margin-bottom": "1rem"
                }
            },
            icon
        ),
        html.h3(
            {
                "style": {
                    "color": "#1e293b",
                    "font-size": "1.2rem",
                    "font-weight": "600",
                    "margin-bottom": "0.5rem"
                }
            },
            title
        ),
        html.p(
            {
                "style": {
                    "color": "#64748b",
                    "margin": "0",
                    "font-size": "0.9rem"
                }
            },
            description
        )
    )

@component
def App():
    return SearchInterface()

app = FastAPI()
configure(app, App)

if __name__ == "__main__":
    run(App, host="127.0.0.1", port=8000)
