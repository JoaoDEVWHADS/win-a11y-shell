#!/usr/bin/env bash
# deploy.sh — Compila a interface Windows 11 React e atualiza /opt/win-a11y-shell
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WIN11_SRC="$SCRIPT_DIR/src/win11"
OPT_DIR="/opt/win-a11y-shell"

echo "[deploy] Verificando diretório fonte do Windows 11: $WIN11_SRC"
if [ ! -d "$WIN11_SRC" ]; then
    echo "[deploy] ❌ Diretório src/win11 não encontrado!"
    exit 1
fi

# Garantir Node.js instalado
if ! command -v node >/dev/null 2>&1; then
    echo "[deploy] Instalando Node.js..."
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
    apt-get install -y nodejs
fi

echo "[deploy] Instalando dependências e compilando a interface Windows 11..."
cd "$WIN11_SRC"
npm install --legacy-peer-deps
npm run build

echo "[deploy] Atualizando /opt/win-a11y-shell/ui com os novos arquivos do Windows 11..."
mkdir -p "$OPT_DIR/ui"
rm -rf "$OPT_DIR/ui/*"

if [ -d "$WIN11_SRC/build" ]; then
    cp -r "$WIN11_SRC/build/"* "$OPT_DIR/ui/"
elif [ -d "$WIN11_SRC/dist" ]; then
    cp -r "$WIN11_SRC/dist/"* "$OPT_DIR/ui/"
else
    echo "[deploy] ❌ Pasta de build (build/ ou dist/) não encontrada!"
    exit 1
fi

echo "[deploy] ✅ Interface Windows 11 compilada e implantada com sucesso em $OPT_DIR/ui"

echo "[deploy] Reiniciando os serviços..."
bash "$SCRIPT_DIR/restart.sh"
