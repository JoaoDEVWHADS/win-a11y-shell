#!/usr/bin/env bash
# deploy.sh — Aplica o tema Windows 11 no MATE e sincroniza /opt/win-a11y-shell
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OPT_DIR="/opt/win-a11y-shell"

echo "[deploy] Instalando pacotes MATE & Tema Windows 11..."
bash "$SCRIPT_DIR/install.sh"

echo "[deploy] Sincronizando Orca personalizado..."
mkdir -p "$OPT_DIR"
if [ -d "$SCRIPT_DIR/orca" ]; then
    cp -r "$SCRIPT_DIR/orca" "$OPT_DIR/"
fi

echo "[deploy] Reiniciando MATE + Orca..."
bash "$SCRIPT_DIR/restart.sh"
