"""Resumo do índice: quantos documentos em cada situação e tipo, e o que pede sua atenção.

Uso: python3 scripts/estado.py
"""
from comum import carregar_config, conectar


def main():
    con = conectar(carregar_config())
    total = con.execute("SELECT COUNT(*) FROM documentos").fetchone()[0]
    print(f"Documentos no índice: {total}")
    print("Por situação:")
    for r in con.execute("SELECT situacao, COUNT(*) n FROM documentos GROUP BY situacao ORDER BY n DESC"):
        print(f"  {r['situacao']}: {r['n']}")
    print("Por tipo (classificados):")
    for r in con.execute("SELECT tipo, COUNT(*) n FROM documentos WHERE tipo IS NOT NULL GROUP BY tipo ORDER BY n DESC"):
        print(f"  {r['tipo']}: {r['n']}")
    sem = con.execute("SELECT COUNT(*) FROM documentos WHERE tem_texto = 0").fetchone()[0]
    falta = con.execute("SELECT COUNT(*) FROM documentos WHERE situacao = 'novo' AND tem_texto = 1 "
                        "AND classificado_por IS NULL").fetchone()[0]
    paginas = con.execute("SELECT COUNT(*) FROM paginas").fetchone()[0]
    print(f"Páginas indexadas: {paginas}")
    print(f"Sem texto (escaneados): {sem}")
    print(f"Esperando classificação: {falta}")
    print("Sensíveis (texto fora do índice):")
    for r in con.execute("SELECT caminho, motivo FROM documentos WHERE sensivel = 1"):
        print(f"  {r['caminho']}  ({r['motivo'] or 'pelo conteúdo'})")


if __name__ == "__main__":
    main()
