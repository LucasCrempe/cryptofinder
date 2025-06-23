import sqlite3

# Conecta ao banco
conn = sqlite3.connect("criptomoedas.db")
cursor = conn.cursor()

print("🔎 Sistema de busca de criptomoedas")
print("Digite 'sair' a qualquer momento para encerrar.\n")

while True:
    tipo_busca = input("Deseja buscar por [id], [nome] ou [simbolo]? ").strip().lower()
    if tipo_busca == "sair":
        break
    if tipo_busca not in ["id", "nome", "simbolo"]:
        print("❌ Opção inválida. Tente novamente.\n")
        continue

    termo = input(f"Digite o {tipo_busca} da criptomoeda: ").strip().lower()
    if termo == "sair":
        break

    # Consulta SQL dinâmica
    query = f"SELECT * FROM moedas WHERE LOWER({tipo_busca}) LIKE ?"
    cursor.execute(query, (f"%{termo}%",))
    resultados = cursor.fetchall()

    if not resultados:
        print("❌ Nenhuma moeda encontrada com esse termo.\n")
        continue

    print(f"\n✅ {len(resultados)} moeda(s) encontrada(s):")
    for i, moeda in enumerate(resultados, start=1):
        print(f"{i}. {moeda[1]} ({moeda[2]})")

    escolha = input("\nDigite o número da moeda que deseja ver os detalhes: ").strip()
    if escolha.lower() == "sair":
        break
    if not escolha.isdigit() or not (1 <= int(escolha) <= len(resultados)):
        print("❌ Número inválido.\n")
        continue

    moeda = resultados[int(escolha) - 1]
    print("\n📊 Dados da moeda selecionada:")
    print(f"🔹 ID: {moeda[0]}")
    print(f"🔹 Nome: {moeda[1]}")
    print(f"🔹 Símbolo: {moeda[2]}")
    print(f"🔹 Preço em USD: ${moeda[3]:,.8f}")
    print(f"🔹 Variação 24h: {moeda[4]:.2f}%")
    print(f"🔹 Market Cap: ${moeda[5]:,.2f}")
    print(f"🔹 Última atualização: {moeda[6]}")
    print("-" * 40)

print("\n✅ Busca finalizada.")
conn.close()
