import sqlite3
import pandas as pd
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import pickle

nltk.download("punkt")
nltk.download("punkt_tab")
nltk.download("stopwords")

# === 1. Carregar dados do SQLite ===
conn = sqlite3.connect('criptomoedas.db')
df = pd.read_sql_query("SELECT id, nome, simbolo FROM moedas", conn)
conn.close()

# === 2. Pré-processamento e criação do índice ===
indice_invertido = {}
stopwords_pt = set(stopwords.words('portuguese'))

for _, linha in df.iterrows():
    termos = word_tokenize(linha['nome'].lower()) + word_tokenize(linha['simbolo'].lower())
    termos = [t for t in termos if t.isalnum() and t not in stopwords_pt]

    for termo in termos:
        if termo not in indice_invertido:
            indice_invertido[termo] = set()
        indice_invertido[termo].add(linha['id'])

# Converte sets para listas (para salvar no pickle)
indice_invertido = {k: list(v) for k, v in indice_invertido.items()}

# === 3. Salvar o índice invertido com Pickle ===
with open("indice_invertido.pkl", "wb") as f:
    pickle.dump(indice_invertido, f)

print("✅ Índice invertido criado e salvo com sucesso.")
