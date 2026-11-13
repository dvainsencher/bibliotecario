"""Lista os arquivos das pastas de origem e grava no índice. Não abre, não move e não altera nada.

Uso:
  python3 scripts/inventario.py            # pastas de origem do config.json
  python3 scripts/inventario.py PASTA...   # outras pastas
  python3 scripts/inventario.py --entrada  # só a pasta _entrada/ do acervo

Arquivo que sumiu do lugar registrado e aparece em outro (mesmo hash) é reencontrado: o índice
passa a apontar para o lugar novo, sem criar duplicata. Para achar arquivos renomeados ou movidos
dentro do acervo, rode com a pasta do acervo.
"""
import datetime
import os
import sys
from pathlib import Path

from comum import EXTENSOES, agora, carregar_config, conectar, parece_sensivel, sha256

MOSTRAR = 20  # caminhos sumidos listados um a um


def main():
    cfg = carregar_config()
    args = sys.argv[1:]
    if args == ["--entrada"]:
        pastas = [str(Path(cfg["acervo"]) / "_entrada")]
    else:
        pastas = args or cfg["origens"]
    con = conectar(cfg)
    novos = dup = sens = ignorados = reencontrados = 0
    for pasta in pastas:
        if not Path(pasta).is_dir():
            print(f"Pasta não encontrada: {pasta}")
            continue
        for raiz, dirs, arquivos in os.walk(pasta):
            # _desfeitos/ guarda cópias desfeitas: não entram no índice
            dirs[:] = sorted(d for d in dirs if not d.startswith(".") and d != "_desfeitos")
            for nome in sorted(arquivos):
                if nome.startswith("."):
                    continue
                caminho = Path(raiz) / nome
                if caminho.suffix.lower() not in EXTENSOES:
                    ignorados += 1
                    continue
                # Já no índice: no lugar de agora ou no de origem (depois de copiado para o acervo)
                if con.execute("SELECT 1 FROM documentos WHERE caminho = ? OR caminho_origem = ?",
                               (str(caminho), str(caminho))).fetchone():
                    continue
                h = sha256(caminho)
                sumido = next((r for r in con.execute("SELECT id, caminho FROM documentos WHERE sha256 = ? ORDER BY id",
                                                      (h,)) if not Path(r["caminho"]).exists()), None)
                if sumido:
                    con.execute("UPDATE documentos SET caminho = ? WHERE id = ?", (str(caminho), sumido["id"]))
                    con.execute("INSERT INTO movimentos (documento_id, sha256, origem, destino, operacao, motivo, feito_em) "
                                "VALUES (?, ?, ?, ?, 'reencontrado', ?, ?)",
                                (sumido["id"], h, sumido["caminho"], str(caminho),
                                 "movido ou renomeado fora do bibliotecário", agora()))
                    print(f"Reencontrado: {sumido['caminho']}  ->  {caminho}")
                    reencontrados += 1
                    continue
                termo = parece_sensivel(caminho.relative_to(pasta))
                igual = con.execute(
                    "SELECT id FROM documentos WHERE sha256 = ? AND situacao != 'duplicata' ORDER BY id LIMIT 1",
                    (h,)).fetchone()
                situacao, motivo, dup_de = "novo", None, None
                if termo:
                    situacao, motivo = "sensivel", f"nome ou pasta contém '{termo}'"
                    sens += 1
                elif igual:
                    situacao, motivo, dup_de = "duplicata", "arquivo idêntico, mesmo hash", igual["id"]
                    dup += 1
                info = caminho.stat()
                modificado = datetime.datetime.fromtimestamp(info.st_mtime).isoformat(timespec="seconds")
                con.execute(
                    """INSERT INTO documentos (sha256, caminho, caminho_origem, nome_original, extensao,
                       tamanho, modificado_em, sensivel, situacao, motivo, duplicata_de, indexado_em)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (h, str(caminho), str(caminho), nome, caminho.suffix.lower(), info.st_size, modificado,
                     1 if termo else 0, situacao, motivo, dup_de, agora()))
                novos += 1
    con.commit()
    sumidos = [r["caminho"] for r in con.execute("SELECT caminho FROM documentos ORDER BY id")
               if not Path(r["caminho"]).exists()]
    print(f"Arquivos novos no índice: {novos}")
    print(f"  duplicados idênticos: {dup}")
    print(f"  sensíveis pelo nome (texto não será lido): {sens}")
    print(f"Ignorados por extensão (não são PDF, DOCX, TXT ou MD): {ignorados}")
    if reencontrados:
        print(f"Reencontrados em outro lugar: {reencontrados}")
    if sumidos:
        print(f"Caminhos no índice que não existem mais: {len(sumidos)}"
              " (o arquivo foi movido, renomeado ou apagado fora do bibliotecário)")
        for c in sumidos[:MOSTRAR]:
            print(f"  {c}")
        if len(sumidos) > MOSTRAR:
            print(f"  ... e mais {len(sumidos) - MOSTRAR}. Se forem muitos, confira se a pasta ou o disco"
                  " está conectado.")
        print("Se algum foi renomeado ou movido para dentro do acervo, rode: "
              "python3 scripts/inventario.py PASTA_DO_ACERVO")


if __name__ == "__main__":
    main()
