#!/usr/bin/env bash
# deploy.sh — copia src/ para /opt/win-a11y-shell e reinicia tudo do zero
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_DIR="$SCRIPT_DIR/src"
OPT_DIR="/opt/win-a11y-shell"

echo "[deploy] Verificando diretório fonte: $SRC_DIR"
if [ ! -d "$SRC_DIR" ]; then
    echo "[deploy] ❌ Diretório src/ não encontrado!"
    exit 1
fi

echo "[deploy] Verificando sintaxe Python de todos os arquivos..."
ERRORS=0
for f in "$SRC_DIR"/*.py; do
    if ! python3 -m py_compile "$f" 2>/dev/null; then
        echo "[deploy] ❌ Erro de sintaxe em: $f"
        python3 -m py_compile "$f"
        ERRORS=$((ERRORS + 1))
    fi
done

if [ $ERRORS -gt 0 ]; then
    echo "[deploy] ❌ Abortando deploy: $ERRORS arquivo(s) com erro de sintaxe."
    exit 1
fi
echo "[deploy] ✅ Sintaxe OK em todos os arquivos."

echo "[deploy] Copiando arquivos para $OPT_DIR..."
cp "$SRC_DIR"/*.py "$OPT_DIR/"
echo "[deploy] ✅ Arquivos copiados:"
ls "$OPT_DIR"/*.py | xargs -I{} basename {}

echo "[deploy] Reiniciando daemon..."
bash "$SCRIPT_DIR/restart.sh"
