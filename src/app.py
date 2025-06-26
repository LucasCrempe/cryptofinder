from reactpy import component, html, hooks, run
from reactpy.backend.fastapi import configure
from fastapi import FastAPI
import sqlite3
import pickle
from typing import List, Tuple, Set, Optional
from pathlib import Path
import asyncio

# Classe de busca adaptada para uso assíncrono
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
        except (FileNotFoundError, Exception):
            return False
    
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
    
    def search_cryptocurrencies(self, term: str) -> List[Tuple]:
        if self.index_loaded:
            found_ids = self._search_ids_by_term(term)
            if not found_ids:
                return []
            
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                placeholders = ','.join(['?' for _ in found_ids])
                query = f"""
                    SELECT * FROM moedas 
                    WHERE id IN ({placeholders}) 
                    ORDER BY market_cap DESC NULLS LAST
                """
                cursor.execute(query, list(found_ids))
                results = cursor.fetchall()
                conn.close()
                return results
            except sqlite3.Error:
                return []
        else:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                query = """
                    SELECT * FROM moedas 
                    WHERE LOWER(nome) LIKE ? OR LOWER(simbolo) LIKE ? OR LOWER(id) LIKE ?
                    ORDER BY market_cap DESC
                """
                cursor.execute(query, (f"%{term.lower()}%", f"%{term.lower()}%", f"%{term.lower()}%"))
                results = cursor.fetchall()
                conn.close()
                return results
            except sqlite3.Error:
                return []
    
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

# Instância global do motor de busca
search_engine = CryptoSearchEngine()

@component
def SearchBar():
    search_term, set_search_term = hooks.use_state("")
    results, set_results = hooks.use_state([])
    loading, set_loading = hooks.use_state(False)
    selected_crypto, set_selected_crypto = hooks.use_state(None)
    
    async def handle_search():
        if not search_term.strip():
            set_results([])
            return
        
        set_loading(True)
        # Simular busca assíncrona
        await asyncio.sleep(0.1)
        search_results = search_engine.search_cryptocurrencies(search_term)
        set_results(search_results)
        set_loading(False)
    
    def handle_input_change(event):
        value = event["target"]["value"]
        set_search_term(value)
        if not value.strip():
            set_results([])
            set_selected_crypto(None)
    
    def handle_crypto_select(crypto):
        set_selected_crypto(crypto)
    
    def handle_back():
        set_selected_crypto(None)
    
    return html.div(
        {
            "style": {
                "min-height": "100vh",
                "background": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                "padding": "2rem",
                "font-family": "'Inter', -apple-system, BlinkMacSystemFont, sans-serif"
            }
        },
        html.div(
            {
                "style": {
                    "max-width": "1200px",
                    "margin": "0 auto"
                }
            },
            # Header
            html.div(
                {
                    "style": {
                        "text-align": "center",
                        "margin-bottom": "3rem"
                    }
                },
                html.h1(
                    "CryptoFinder",
                    {
                        "style": {
                            "color": "white",
                            "font-size": "3.5rem",
                            "font-weight": "700",
                            "margin": "0 0 0.5rem 0",
                            "text-shadow": "0 4px 8px rgba(0,0,0,0.3)"
                        }
                    }
                ),
                html.p(
                    "Encontre informações detalhadas sobre criptomoedas",
                    {
                        "style": {
                            "color": "rgba(255,255,255,0.9)",
                            "font-size": "1.2rem",
                            "margin": "0",
                            "font-weight": "300"
                        }
                    }
                )
            ),
            
            # Search Container
            html.div(
                {
                    "style": {
                        "background": "white",
                        "border-radius": "20px",
                        "box-shadow": "0 20px 40px rgba(0,0,0,0.1)",
                        "overflow": "hidden",
                        "backdrop-filter": "blur(10px)"
                    }
                },
                # Search Input
                html.div(
                    {
                        "style": {
                            "padding": "2rem",
                            "border-bottom": "1px solid #f0f0f0" if results else "none"
                        }
                    },
                    html.div(
                        {
                            "style": {
                                "position": "relative",
                                "display": "flex",
                                "align-items": "center"
                            }
                        },
                        html.input(
                            {
                                "type": "text",
                                "placeholder": "Buscar por nome, símbolo ou ID (ex: Bitcoin, BTC, bitcoin)",
                                "value": search_term,
                                "on_input": handle_input_change,
                                "on_key_down": lambda event: handle_search() if event["key"] == "Enter" else None,
                                "style": {
                                    "width": "100%",
                                    "padding": "1rem 1.5rem",
                                    "font-size": "1.1rem",
                                    "border": "2px solid #e2e8f0",
                                    "border-radius": "50px",
                                    "outline": "none",
                                    "transition": "all 0.3s ease",
                                    "background": "#f8fafc"
                                }
                            }
                        ),
                        html.button(
                            "🔍" if not loading else "⏳",
                            {
                                "on_click": lambda _: handle_search(),
                                "disabled": loading,
                                "style": {
                                    "position": "absolute",
                                    "right": "8px",
                                    "background": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                                    "color": "white",
                                    "border": "none",
                                    "border-radius": "50%",
                                    "width": "45px",
                                    "height": "45px",
                                    "cursor": "pointer" if not loading else "not-allowed",
                                    "font-size": "1.2rem",
                                    "transition": "all 0.3s ease",
                                    "opacity": "0.8" if loading else "1"
                                }
                            }
                        )
                    )
                ),
                
                # Results or Details
                CryptoDetails(selected_crypto, handle_back) if selected_crypto else CryptoResults(results, loading, handle_crypto_select)
            )
        )
    )

@component
def CryptoResults(results, loading, on_select):
    if loading:
        return html.div(
            {
                "style": {
                    "padding": "3rem",
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
                "Buscando criptomoedas...",
                {
                    "style": {
                        "margin-top": "1rem",
                        "color": "#64748b",
                        "font-size": "1.1rem"
                    }
                }
            ),
            html.style("""
                @keyframes spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }
            """)
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
                    "padding": "1rem 2rem",
                    "background": "#f8fafc",
                    "border-bottom": "1px solid #e2e8f0"
                }
            },
            html.h3(
                f"{len(results)} resultado{'s' if len(results) != 1 else ''} encontrado{'s' if len(results) != 1 else ''}",
                {
                    "style": {
                        "margin": "0",
                        "color": "#1e293b",
                        "font-size": "1.1rem",
                        "font-weight": "600"
                    }
                }
            )
        ),
        *[CryptoCard(crypto, on_select) for crypto in results[:20]]
    )

@component
def CryptoCard(crypto, on_select):
    # crypto = (id, nome, simbolo, preco_usd, variacao_24h, market_cap, ultima_atualizacao)
    price = search_engine.format_currency_value(crypto[3], 'price')
    change = search_engine.format_currency_value(crypto[4], 'change')
    market_cap = search_engine.format_currency_value(crypto[5], 'market_cap')
    
    change_color = "#10b981" if crypto[4] and crypto[4] > 0 else "#ef4444" if crypto[4] and crypto[4] < 0 else "#64748b"
    
    return html.div(
        {
            "on_click": lambda _: on_select(crypto),
            "style": {
                "padding": "1.5rem 2rem",
                "border-bottom": "1px solid #f1f5f9",
                "cursor": "pointer",
                "transition": "all 0.2s ease",
                "display": "flex",
                "justify-content": "space-between",
                "align-items": "center"
            },
            "on_mouse_enter": lambda _: None,
            "on_mouse_leave": lambda _: None
        },
        html.div(
            {
                "style": {
                    "flex": "1"
                }
            },
            html.div(
                {
                    "style": {
                        "display": "flex",
                        "align-items": "center",
                        "margin-bottom": "0.5rem"
                    }
                },
                html.h4(
                    crypto[1] or "N/A",
                    {
                        "style": {
                            "margin": "0 0.5rem 0 0",
                            "font-size": "1.1rem",
                            "font-weight": "600",
                            "color": "#1e293b"
                        }
                    }
                ),
                html.span(
                    (crypto[2] or "").upper(),
                    {
                        "style": {
                            "background": "#e2e8f0",
                            "color": "#475569",
                            "padding": "0.25rem 0.5rem",
                            "border-radius": "12px",
                            "font-size": "0.8rem",
                            "font-weight": "500"
                        }
                    }
                )
            ),
            html.p(
                f"Market Cap: {market_cap}",
                {
                    "style": {
                        "margin": "0",
                        "color": "#64748b",
                        "font-size": "0.9rem"
                    }
                }
            )
        ),
        html.div(
            {
                "style": {
                    "text-align": "right"
                }
            },
            html.div(
                price,
                {
                    "style": {
                        "font-size": "1.2rem",
                        "font-weight": "700",
                        "color": "#1e293b",
                        "margin-bottom": "0.25rem"
                    }
                }
            ),
            html.div(
                change,
                {
                    "style": {
                        "font-size": "0.9rem",
                        "font-weight": "600",
                        "color": change_color
                    }
                }
            )
        )
    )

@component
def CryptoDetails(crypto, on_back):
    if not crypto:
        return html.div()
    
    price = search_engine.format_currency_value(crypto[3], 'price')
    change = search_engine.format_currency_value(crypto[4], 'change')
    market_cap = search_engine.format_currency_value(crypto[5], 'market_cap')
    
    change_color = "#10b981" if crypto[4] and crypto[4] > 0 else "#ef4444" if crypto[4] and crypto[4] < 0 else "#64748b"
    
    return html.div(
        {
            "style": {
                "padding": "2rem"
            }
        },
        # Back button
        html.button(
            "← Voltar aos resultados",
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
                    "font-weight": "500"
                }
            }
        ),
        
        # Crypto header
        html.div(
            {
                "style": {
                    "text-align": "center",
                    "margin-bottom": "2rem"
                }
            },
            html.h2(
                crypto[1] or "N/A",
                {
                    "style": {
                        "margin": "0 0 0.5rem 0",
                        "font-size": "2.5rem",
                        "font-weight": "700",
                        "color": "#1e293b"
                    }
                }
            ),
            html.div(
                (crypto[2] or "").upper(),
                {
                    "style": {
                        "background": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                        "color": "white",
                        "padding": "0.5rem 1rem",
                        "border-radius": "20px",
                        "font-size": "1.1rem",
                        "font-weight": "600",
                        "display": "inline-block"
                    }
                }
            )
        ),
        
        # Price section
        html.div(
            {
                "style": {
                    "text-align": "center",
                    "margin-bottom": "3rem"
                }
            },
            html.div(
                price,
                {
                    "style": {
                        "font-size": "3rem",
                        "font-weight": "700",
                        "color": "#1e293b",
                        "margin-bottom": "0.5rem"
                    }
                }
            ),
            html.div(
                f"Variação 24h: {change}",
                {
                    "style": {
                        "font-size": "1.2rem",
                        "font-weight": "600",
                        "color": change_color
                    }
                }
            )
        ),
        
        # Details grid
        html.div(
            {
                "style": {
                    "display": "grid",
                    "grid-template-columns": "repeat(auto-fit, minmax(250px, 1fr))",
                    "gap": "1.5rem"
                }
            },
            DetailCard("ID", crypto[0] or "N/A"),
            DetailCard("Market Cap", market_cap),
            DetailCard("Última Atualização", crypto[6][:19].replace('T', ' ') if crypto[6] else "N/A")
        )
    )

@component
def DetailCard(title, value):
    return html.div(
        {
            "style": {
                "background": "#f8fafc",
                "padding": "1.5rem",
                "border-radius": "12px",
                "border": "1px solid #e2e8f0"
            }
        },
        html.h4(
            title,
            {
                "style": {
                    "margin": "0 0 0.5rem 0",
                    "color": "#64748b",
                    "font-size": "0.9rem",
                    "font-weight": "500",
                    "text-transform": "uppercase",
                    "letter-spacing": "0.05em"
                }
            }
        ),
        html.p(
            value,
            {
                "style": {
                    "margin": "0",
                    "color": "#1e293b",
                    "font-size": "1.1rem",
                    "font-weight": "600",
                    "word-break": "break-all"
                }
            }
        )
    )

@component
def App():
    return html.div(SearchBar())

# Configuração do servidor
app = FastAPI()
configure(app, App)

if __name__ == "__main__":
    run(App, host="127.0.0.1", port=8000)
