#!/bin/bash

# Script UNIVERSAL para compilar y ejecutar C++ en iTerm desde Zed
# Compila automáticamente todos los archivos .cpp del mismo directorio
# Ubicación: ~/Documents/zed-scripts/compile_and_run_cpp.sh

FILE="$1"

if [ -z "$FILE" ]; then
    echo "Error: No se proporcionó archivo"
    exit 1
fi

DIRNAME=$(dirname "$FILE")
BASENAME=$(basename "$FILE" .cpp)

# Cambiar al directorio del archivo
cd "$DIRNAME"

# Encontrar todos los archivos .cpp en el directorio
CPP_FILES=$(find . -maxdepth 1 -name "*.cpp" -type f)

# Compilar todos los .cpp juntos
echo "Compilando archivos .cpp en $DIRNAME..."
/usr/bin/g++ $CPP_FILES -std=c++17 -o "$BASENAME"

if [ $? -eq 0 ]; then
    echo "Compilación exitosa. Abriendo iTerm..."
    # Si compiló bien, abrir iTerm y ejecutar
    osascript <<EOF
tell application "iTerm"
    activate
    set newWindow to (create window with default profile)
    tell current session of newWindow
        write text "cd '$DIRNAME' && ./'$BASENAME'; echo; echo 'Program finished. Press any key to close...'; read -n 1 -s"
    end tell
end tell
EOF
else
    echo "Error de compilación"
    exit 1
fi
