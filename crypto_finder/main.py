# main.py
from reactpy import component, html, run
from reactpy.backend.fastapi import configure
from fastapi import FastAPI

from pages.home import SearchInterface

@component
def App():
    return html.div(
        {
            "style": {
                "margin": "0",
                "padding": "0",
                "box-sizing": "border-box"
            }
        },
        html.style("""
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            html, body {
                margin: 0 !important;
                padding: 0 !important;
                overflow-x: hidden !important;
            }
        """),
        SearchInterface()
    )

app = FastAPI()
configure(app, App)

# Para executar com uvicorn, comente a linha abaixo.
# Ex: uvicorn main:app --reload
if __name__ == "__main__":
    run(App, host="127.0.0.1", port=8001)

