"""Grava no índice a resposta do subagente classificador.

Uso: python3 scripts/gravar_classificacao.py indice/lotes/lote_001_resposta.jsonl [--modelo haiku]
"""
import json
import sys

from comum import PASTAS, carregar_config, conectar, ler_tags, nome_seguro

TIPOS = set(PASTAS)


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    arquivo = sys.argv[1]
    modelo = sys.argv[sys.argv.index("--modelo") + 1] if "--modelo" in sys.argv else "haiku"
    cfg = carregar_config()
    con = conectar(cfg)
    permitidas = ler_tags()
    gravados = avisos = 0
    with open(arquivo, encoding="utf-8") as f:
        for n, linha in enumerate(f, start=1):
            linha = linha.strip()
            if not linha:
                continue
            try:
                r = json.loads(linha)
            except json.JSONDecodeError:
                print(f"Linha {n}: JSON inválido, ignorada")
                avisos += 1
                continue
            tipo = (r.get("tipo") or "outro").lower()
            if tipo not in TIPOS:
                print(f"Documento {r.get('id')}: tipo '{tipo}' fora da lista, virou 'outro'")
                tipo = "outro"
            tags = [t.lower() for t in (r.get("tags") or []) if t]
            fora = [t for t in tags if t not in permitidas]
            if fora:
                print(f"Documento {r.get('id')}: tags fora da lista descartadas: {', '.join(fora)}")
                avisos += 1
            tags = [t for t in tags if t in permitidas][:6]
            autores = r.get("autores") or []
            if isinstance(autores, str):
                autores = [autores]
            sensivel = bool(r.get("sensivel"))
            con.execute(
                """UPDATE documentos SET tipo = ?, titulo = ?, autores = ?, ano = ?, fonte = ?, doi = ?,
                   idioma = ?, tags = ?, resumo = ?, nome_sugerido = ?, confianca = ?, motivo = ?,
                   classificado_por = ?, sensivel = ?, situacao = ? WHERE id = ?""",
                (tipo, r.get("titulo"), "; ".join(a for a in autores if a), r.get("ano"), r.get("fonte"),
                 r.get("doi"), r.get("idioma"), "; ".join(tags), r.get("resumo"),
                 nome_seguro(r.get("nome_sugerido")), float(r.get("confianca") or 0),
                 r.get("motivo_baixa_confianca"), modelo, 1 if sensivel else 0,
                 "sensivel" if sensivel else "novo", r.get("id")))
            if sensivel:
                # O texto de um documento sensível sai do índice
                con.execute("DELETE FROM paginas WHERE documento_id = ?", (r.get("id"),))
                print(f"Documento {r.get('id')}: marcado como sensível pelo conteúdo, texto removido do índice")
            gravados += 1
    con.commit()
    print(f"Classificações gravadas: {gravados}  avisos: {avisos}")


if __name__ == "__main__":
    main()
