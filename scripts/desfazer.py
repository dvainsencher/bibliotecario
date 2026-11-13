"""Desfaz a última rodada do aplicar.py, sem apagar nada.

Movimento: o arquivo volta para onde estava.
Cópia: a cópia vai para _revisar/_desfeitos/ (o original nunca saiu do lugar).
Uso: python3 scripts/desfazer.py [--simular]
"""
import shutil
import sys
from pathlib import Path

from comum import agora, carregar_config, conectar


def main():
    simular = "--simular" in sys.argv
    cfg = carregar_config()
    con = conectar(cfg)
    ultima = con.execute(
        "SELECT MAX(feito_em) FROM movimentos WHERE operacao IN ('copia', 'move')").fetchone()[0]
    if not ultima:
        print("Nada para desfazer.")
        return
    movs = con.execute(
        "SELECT * FROM movimentos WHERE feito_em = ? AND operacao IN ('copia', 'move')", (ultima,)).fetchall()
    desfeitos = Path(cfg["acervo"]) / "_revisar" / "_desfeitos"
    print(f"Desfazer a rodada de {ultima}: {len(movs)} arquivo(s)")
    rodada = agora()
    for m in movs:
        atual = Path(m["destino"])
        alvo = Path(m["origem"]) if m["operacao"] == "move" else desfeitos / atual.name
        print(f"  {atual}  ->  {alvo}")
        if simular or not atual.exists():
            continue
        alvo.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(atual), str(alvo))
        caminho_doc = str(alvo) if m["operacao"] == "move" else m["origem"]
        con.execute("UPDATE documentos SET caminho = ?, situacao = 'novo' WHERE id = ?",
                    (caminho_doc, m["documento_id"]))
        con.execute("INSERT INTO movimentos (documento_id, sha256, origem, destino, operacao, motivo, feito_em) "
                    "VALUES (?, ?, ?, ?, 'desfaz', ?, ?)",
                    (m["documento_id"], m["sha256"], str(atual), str(alvo), f"desfaz {ultima}", rodada))
        con.execute("UPDATE movimentos SET operacao = operacao || '-desfeita' WHERE id = ?", (m["id"],))
    if simular:
        print("Simulação: nada mudou.")
    else:
        con.commit()


if __name__ == "__main__":
    main()
