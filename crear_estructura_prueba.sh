#!/bin/bash

# Carpeta raíz de prueba.
# Ajusta esta ruta si tu proyecto está en otra ubicación.
BASE_DIR="$HOME/Documents/prueba_carpetas_google_sheet/sedes"

echo "Creando estructura de prueba en:"
echo "$BASE_DIR"

# Crear sedes
mkdir -p "$BASE_DIR/TOMOGRAFIAS COLONIA"
mkdir -p "$BASE_DIR/TOMOGRAFIAS CAUDILLOS"
mkdir -p "$BASE_DIR/TOMOGRAFIAS NUEVO CENTRO"
mkdir -p "$BASE_DIR/TOMOGRAFIAS DURAZNO"

# ============================================================
# TOMOGRAFIAS COLONIA
# ============================================================

# Coincidencia normal: Sofia Araujo
mkdir -p "$BASE_DIR/TOMOGRAFIAS COLONIA/Sofia_Araujo"
touch "$BASE_DIR/TOMOGRAFIAS COLONIA/Sofia_Araujo/estudio_01.dcm"
touch "$BASE_DIR/TOMOGRAFIAS COLONIA/Sofia_Araujo/imagen_01.jpg"

# Mismo nombre, pero separado con guion.
mkdir -p "$BASE_DIR/TOMOGRAFIAS COLONIA/Elena-Reolon"
touch "$BASE_DIR/TOMOGRAFIAS COLONIA/Elena-Reolon/estudio_01.dcm"

# Carpeta vacía.
mkdir -p "$BASE_DIR/TOMOGRAFIAS COLONIA/Alma Ruiz"

# Nombre invertido para probar token_sort_ratio.
mkdir -p "$BASE_DIR/TOMOGRAFIAS COLONIA/Pereira_Daniel"
touch "$BASE_DIR/TOMOGRAFIAS COLONIA/Pereira_Daniel/informe.pdf"

# ============================================================
# TOMOGRAFIAS CAUDILLOS
# ============================================================

# Nombre con espacios.
mkdir -p "$BASE_DIR/TOMOGRAFIAS CAUDILLOS/María Eugenia Rodríguez"
touch "$BASE_DIR/TOMOGRAFIAS CAUDILLOS/María Eugenia Rodríguez/estudio.dcm"

# Nombre sin tilde, para probar normalización de tildes.
mkdir -p "$BASE_DIR/TOMOGRAFIAS CAUDILLOS/Jose Gonzalez"
touch "$BASE_DIR/TOMOGRAFIAS CAUDILLOS/Jose Gonzalez/imagen.png"

# Nombre con una diferencia pequeña: útil para similitud probable.
mkdir -p "$BASE_DIR/TOMOGRAFIAS CAUDILLOS/Camila Scaronne"
touch "$BASE_DIR/TOMOGRAFIAS CAUDILLOS/Camila Scaronne/estudio_01.dcm"

# ============================================================
# TOMOGRAFIAS NUEVO CENTRO
# ============================================================

# Nombre compuesto con guiones bajos.
mkdir -p "$BASE_DIR/TOMOGRAFIAS NUEVO CENTRO/Juan_Carlos_Perez"
touch "$BASE_DIR/TOMOGRAFIAS NUEVO CENTRO/Juan_Carlos_Perez/archivo_01.dcm"
touch "$BASE_DIR/TOMOGRAFIAS NUEVO CENTRO/Juan_Carlos_Perez/archivo_02.dcm"

# Nombre invertido y con guiones.
mkdir -p "$BASE_DIR/TOMOGRAFIAS NUEVO CENTRO/Gonzalez-Maria"
mkdir -p "$BASE_DIR/TOMOGRAFIAS NUEVO CENTRO/Gonzalez-Maria/imagenes"
touch "$BASE_DIR/TOMOGRAFIAS NUEVO CENTRO/Gonzalez-Maria/imagenes/radiografia.jpg"

# Caso que no debería encontrarse en la hoja.
mkdir -p "$BASE_DIR/TOMOGRAFIAS NUEVO CENTRO/Persona No Registrada"
touch "$BASE_DIR/TOMOGRAFIAS NUEVO CENTRO/Persona No Registrada/archivo.txt"

# ============================================================
# TOMOGRAFIAS DURAZNO
# ============================================================

# Carpeta vacía.
mkdir -p "$BASE_DIR/TOMOGRAFIAS DURAZNO/Freddy Pereira"

# Nombre con guion y contenido.
mkdir -p "$BASE_DIR/TOMOGRAFIAS DURAZNO/Daniel-Maciel"
touch "$BASE_DIR/TOMOGRAFIAS DURAZNO/Daniel-Maciel/estudio.dcm"

# Nombre con formato inconsistente.
mkdir -p "$BASE_DIR/TOMOGRAFIAS DURAZNO/RODRIGUEZ__MARIA_EUGENIA"
touch "$BASE_DIR/TOMOGRAFIAS DURAZNO/RODRIGUEZ__MARIA_EUGENIA/archivo.pdf"

echo ""
echo "Estructura creada correctamente."
echo ""
echo "Puedes revisarla con:"
echo "find \"$BASE_DIR\" -maxdepth 3 -print"