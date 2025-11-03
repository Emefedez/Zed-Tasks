#!/bin/bash
# Uso: ghidra_headless.sh <dir_del_archivo_activo> <stem_del_archivo>
set -euo pipefail

DIR="${1:-}"
STEM="${2:-}"

if [[ -z "$DIR" || -z "$STEM" ]]; then
  echo "Uso: $0 <dir> <stem>" >&2
  exit 2
fi

BIN="$DIR/$STEM"
if [[ ! -f "$BIN" ]]; then
  echo "No existe el binario '$BIN'. Compílalo primero y vuelve a ejecutar." >&2
  exit 3
fi

# Dónde guardar el proyecto de Ghidra (puedes override con GHIDRA_PROJECT_DIR / GHIDRA_PROJECT_NAME)
PROJ_DIR="${GHIDRA_PROJECT_DIR:-$HOME/Documents/GhidraProjects}"
DEFAULT_NAME="$(basename "$(dirname "$DIR")")"   # carpeta padre de DIR, p.ej. 'EstadisticasFogar'
PROJ_NAME="${GHIDRA_PROJECT_NAME:-$DEFAULT_NAME}"
mkdir -p "$PROJ_DIR"

# Carpeta de salida para decompilación en la raíz del repo
ROOT_DIR="$(dirname "$DIR")"
OUT_DIR="$ROOT_DIR/🔎 Decompiled!"
mkdir -p "$OUT_DIR"

# Localizar analyzeHeadless
find_analyze_headless() {
  if command -v brew >/dev/null 2>&1; then
    local p
    p="$(brew --prefix ghidra 2>/dev/null || true)"
    if [[ -n "$p" && -x "$p/libexec/support/analyzeHeadless" ]]; then
      echo "$p/libexec/support/analyzeHeadless"; return 0
    fi
    if [[ -x "/opt/homebrew/opt/ghidra/libexec/support/analyzeHeadless" ]]; then
      echo "/opt/homebrew/opt/ghidra/libexec/support/analyzeHeadless"; return 0
    fi
  fi
  if [[ -x "/opt/homebrew/Cellar/ghidra/11.4.2/libexec/support/analyzeHeadless" ]]; then
    echo "/opt/homebrew/Cellar/ghidra/11.4.2/libexec/support/analyzeHeadless"; return 0
  fi
  if [[ -x "/Applications/Ghidra.app/Contents/MacOS/support/analyzeHeadless" ]]; then
    echo "/Applications/Ghidra.app/Contents/MacOS/support/analyzeHeadless"; return 0
  fi
  return 1
}

GHIDRA_BIN="$(find_analyze_headless || true)"
if [[ -z "$GHIDRA_BIN" ]]; then
  echo "No encuentro analyzeHeadless. Instala Ghidra o ajusta la ruta." >&2
  exit 127
fi

# Dónde está el script de Ghidra (Jython)
SCRIPT_DIR="${GHIDRA_SCRIPT_DIR:-$HOME/Documents/zed-scripts/ghidra_scripts}"
SCRIPT_FILE="DecompileAndReport.py"

echo "Usando analyzeHeadless en: $GHIDRA_BIN"
echo "Proyecto: $PROJ_DIR / $PROJ_NAME"
echo "Importando binario: $BIN"
echo "Decompiled dir: $OUT_DIR"

# Ejecutar análisis y postScript con argumentos clave-valor
"$GHIDRA_BIN" "$PROJ_DIR" "$PROJ_NAME" \
  -import "$BIN" -overwrite \
  -scriptPath "$SCRIPT_DIR" \
  -postScript "$SCRIPT_FILE" outDir "$OUT_DIR" projectPath "$PROJ_DIR/$PROJ_NAME.gpr" programPath "$BIN"

echo "Listo. Proyecto en: $PROJ_DIR/$PROJ_NAME.gpr"
echo "Decompilación en: $OUT_DIR"
