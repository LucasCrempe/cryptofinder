# pages/home.py
from reactpy import component, html, hooks

from backend.search import search_engine
from utils.formatting import get_placeholder, get_search_type_label
from components.header import Header
from components.search_type_button import SearchTypeButton
from components.results_section import ResultsSection
from .about import AboutPage

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
    
    search_types = ["inverted_index", "id", "name", "symbol"]
    search_labels = {
        "inverted_index": "Smart Search",
        "id": "Search by ID", 
        "name": "Search by Name",
        "symbol": "Search by Symbol"
    }
    
    # ... (código do return de SearchInterface exatamente como no original)
    return html.div(...)
