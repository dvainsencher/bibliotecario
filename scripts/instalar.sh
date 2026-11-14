#!/usr/bin/env bash
# Confere e instala o que o bibliotecário precisa, em Mac ou Linux.
# Pode rodar quantas vezes quiser: só instala o que falta.
#
# Uso (um comando só):
#   curl -fsSL https://raw.githubusercontent.com/dvainsencher/bibliotecario/main/scripts/instalar.sh | bash
#
# Não usa Homebrew, não pede senha e não compila nada. O pdftotext (poppler) e
# o Python 3.12 vêm prontos do conda-forge, via micromamba, numa pasta só:
# ~/projetos-ia/.ambiente (para desinstalar, apague essa pasta).
#
# Variáveis opcionais:
#   BIBLIOTECARIO_DIR        usa esta pasta do bibliotecário em vez de baixar
#   INSTALAR_FORCAR_PYTHON=1 usa o Python do ambiente mesmo que o do sistema sirva (teste)

set -u

PASTA_PROJ="${PROJETOS_IA:-$HOME/projetos-ia}"
AMBIENTE="$PASTA_PROJ/.ambiente"
RAIZ_MAMBA="$PASTA_PROJ/.mamba"
BIN="$HOME/.local/bin"
BIBLIO="${BIBLIOTECARIO_DIR:-$PASTA_PROJ/bibliotecario}"
PROBLEMAS=0
MANUAIS=0

mkdir -p "$BIN" "$PASTA_PROJ"
export PATH="$BIN:$PATH"

ok()     { printf '  [ok]          %s\n' "$1"; }
falta()  { printf '  [falta]       %s\n' "$1"; }
fazendo(){ printf '  [instalando]  %s\n' "$1"; }
aviso()  { printf '  [atenção]     %s\n' "$1"; }
erro()   { printf '  [erro]        %s\n' "$1"; PROBLEMAS=$((PROBLEMAS + 1)); }

pdftotext_serve() {
  command -v pdftotext >/dev/null 2>&1 && pdftotext -v >/dev/null 2>&1
}

# Serve: Python 3.9 ou mais novo, com SQLite FTS5.
python_serve() {
  command -v "$1" >/dev/null 2>&1 && "$1" -c '
import sys, sqlite3
c = sqlite3.connect(":memory:")
c.execute("create virtual table t using fts5(x)")
sys.exit(0 if sys.version_info >= (3, 9) else 1)
' >/dev/null 2>&1
}

echo
echo "Conferindo o seu computador"
echo

SO="$(uname -s)"
ARQ="$(uname -m)"
case "$SO-$ARQ" in
  Darwin-arm64)   PLAT="osx-arm64";    NOME="Mac com chip Apple" ;;
  Darwin-x86_64)  PLAT="osx-64";       NOME="Mac com chip Intel" ;;
  Linux-x86_64)   PLAT="linux-64";     NOME="Linux x86_64" ;;
  Linux-aarch64)  PLAT="linux-aarch64"; NOME="Linux ARM" ;;
  *) echo "Sistema não suportado: $SO $ARQ"; exit 1 ;;
esac

if [ "$SO" = "Darwin" ]; then
  VERSAO_MAC="$(sw_vers -productVersion)"
  ok "$NOME, macOS $VERSAO_MAC"
  if [ "${VERSAO_MAC%%.*}" -lt 13 ] 2>/dev/null; then
    aviso "o Claude Code pede macOS 13 ou mais novo"
  fi
else
  ok "$NOME"
fi

# --- Git e Claude Code: só conferir ---
if command -v git >/dev/null 2>&1; then
  ok "git $(git --version | awk '{print $3}')"
else
  falta "git"
  if [ "$SO" = "Darwin" ]; then
    echo "                Rode: xcode-select --install   (abre uma janela, aceite e espere)"
  else
    echo "                Instale o git pelo gerenciador de pacotes da sua distribuição."
  fi
  MANUAIS=$((MANUAIS + 1))
fi

if command -v claude >/dev/null 2>&1; then
  ok "Claude Code $(claude --version 2>/dev/null | head -1)"
else
  falta "Claude Code"
  echo "                Rode: curl -fsSL https://claude.ai/install.sh | bash"
  MANUAIS=$((MANUAIS + 1))
fi

# --- Python e pdftotext ---
PRECISA_PYTHON=0
PRECISA_PDF=0

if [ "${INSTALAR_FORCAR_PYTHON:-0}" = "1" ]; then
  PRECISA_PYTHON=1
  aviso "modo de teste: usando o Python do ambiente"
elif python_serve python3; then
  ok "Python $(python3 --version | awk '{print $2}') com busca FTS5"
else
  falta "Python 3.9 ou mais novo com busca FTS5"
  PRECISA_PYTHON=1
fi

if pdftotext_serve; then
  ok "pdftotext (poppler)"
else
  falta "pdftotext (poppler)"
  PRECISA_PDF=1
fi

# --- Instalar o que falta ---
if [ "$PRECISA_PYTHON" = "1" ] || [ "$PRECISA_PDF" = "1" ]; then
  echo
  echo "Instalando o que falta (alguns minutos, sem senha)"
  echo

  if ! command -v micromamba >/dev/null 2>&1; then
    fazendo "micromamba (gerenciador de pacotes, um arquivo só)"
    TMP="$(mktemp -d)"
    if curl -fsSL "https://micro.mamba.pm/api/micromamba/$PLAT/latest" | tar -xj -C "$TMP" bin/micromamba \
       && mv "$TMP/bin/micromamba" "$BIN/micromamba" && chmod +x "$BIN/micromamba"; then
      ok "micromamba instalado em $BIN"
    else
      erro "não consegui baixar o micromamba. Confira a internet e rode de novo."
    fi
    rm -rf "$TMP"
  fi

  if command -v micromamba >/dev/null 2>&1; then
    if [ ! -x "$AMBIENTE/bin/pdftotext" ] || [ ! -x "$AMBIENTE/bin/python" ]; then
      fazendo "Python 3.12 e poppler (já compilados, do conda-forge)"
      if MAMBA_ROOT_PREFIX="$RAIZ_MAMBA" micromamba create -y -q -p "$AMBIENTE" \
           -c conda-forge --override-channels python=3.12 poppler; then
        ok "ambiente criado em $AMBIENTE"
      else
        erro "não consegui criar o ambiente. Rode de novo; se repetir, mande a tela no grupo."
      fi
    fi

    ligar() {  # ligar NOME: cria um atalho em ~/.local/bin que chama o programa do ambiente
      if [ -x "$AMBIENTE/bin/$1" ]; then
        printf '#!/bin/sh\nexec "%s/bin/%s" "$@"\n' "$AMBIENTE" "$1" > "$BIN/$1"
        chmod +x "$BIN/$1"
      fi
    }
    [ "$PRECISA_PDF" = "1" ] && { ligar pdftotext; ligar pdfinfo; }
    [ "$PRECISA_PYTHON" = "1" ] && { ligar python3; ligar python; }
  fi
fi

# --- Deixar ~/.local/bin no PATH nos próximos Terminais ---
LINHA='export PATH="$HOME/.local/bin:$PATH"'
for ARQUIVO in "$HOME/.zshrc" "$HOME/.bashrc"; do
  if [ "$ARQUIVO" = "$HOME/.zshrc" ] && [ "$SO" != "Darwin" ] && [ ! -f "$ARQUIVO" ]; then continue; fi
  if ! grep -qF '.local/bin' "$ARQUIVO" 2>/dev/null; then
    printf '\n%s\n' "$LINHA" >> "$ARQUIVO"
  fi
done

# --- Conferir de novo ---
echo
echo "Conferindo o resultado"
echo
if python_serve python3; then
  ok "Python $(python3 --version | awk '{print $2}') com busca FTS5"
else
  erro "Python ainda não serve"
fi
if pdftotext_serve; then
  ok "pdftotext (poppler)"
else
  erro "pdftotext ainda não responde"
fi

# --- Bibliotecário e teste ---
if [ ! -d "$BIBLIO" ]; then
  if command -v git >/dev/null 2>&1; then
    fazendo "bibliotecário em $BIBLIO"
    git clone -q https://github.com/dvainsencher/bibliotecario.git "$BIBLIO" || erro "não consegui baixar o bibliotecário"
  fi
fi

if [ -f "$BIBLIO/testes/rodar_teste.py" ]; then
  if SAIDA="$(cd "$BIBLIO" && python3 testes/rodar_teste.py 2>&1)"; then
    ok "teste do bibliotecário: $(printf '%s\n' "$SAIDA" | tail -1)"
  else
    erro "o teste do bibliotecário falhou"
    printf '%s\n' "$SAIDA" | tail -15
  fi
fi

echo
if [ "$PROBLEMAS" -gt 0 ]; then
  echo "Deu erro em $PROBLEMAS item(ns). Leia as linhas [erro] acima."
  exit 1
elif [ "$MANUAIS" -gt 0 ]; then
  echo "O que o script instala está pronto. Falta instalar à mão o que aparece como [falta] acima."
else
  echo "Tudo pronto. Feche e abra o Terminal antes de continuar."
fi
