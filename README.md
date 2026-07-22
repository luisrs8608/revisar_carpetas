# Comparador de Carpetas y Google Sheets

Este proyecto analiza una estructura de carpetas organizada por **sedes**, compara los nombres de las carpetas de personas contra una Google Sheet y genera un libro Excel con varias vistas del resultado.

El objetivo es detectar si cada persona encontrada en las carpetas aparece en la hoja de cálculo, aun cuando el nombre tenga diferencias de formato, como espacios, guiones, guiones bajos, tildes o el orden de nombre y apellido.

---

## Qué hace el script

El script realiza estas tareas:

1. Recorre un directorio principal.
2. Considera cada carpeta directa dentro de ese directorio como una **sede**.
3. Considera cada carpeta directa dentro de una sede como una **persona**.
4. Cuenta si la carpeta de la persona está vacía, cuántos archivos contiene y cuántas subcarpetas tiene.
5. Lee registros de una Google Sheet.
6. Usa la columna `NOMBRE` para comparar contra el nombre de cada carpeta.
7. Lee la columna `FECHA`.
8. Lee la columna `MINUTOS INF` e indica si contiene un entero mayor que cero.
9. Calcula un porcentaje de similitud entre los nombres.
10. Genera un archivo Excel con la salida completa y tres hojas filtradas.

---

## Estructura esperada de carpetas

El directorio principal debe contener carpetas de sedes. Dentro de cada sede deben estar las carpetas de personas.

Ejemplo:

```text
sedes/
├── TOMOGRAFIAS COLONIA/
│   ├── Sofia_Araujo/
│   ├── Elena-Reolon/
│   └── Alma Ruiz/
│
├── TOMOGRAFIAS DURAZNO/
│   ├── Perez_Juan/
│   └── Maria_Eugenia_Rodriguez/
│
└── TOMOGRAFIAS NUEVO CENTRO/
    └── Juan-Carlos-Perez/
```

Los nombres de las carpetas pueden incluir:

- Espacios: `Sofia Araujo`
- Guiones bajos: `Sofia_Araujo`
- Guiones: `Sofia-Araujo`
- Mayúsculas: `SOFIA ARAUJO`
- Tildes o ausencia de tildes: `José González` / `Jose Gonzalez`
- Orden diferente de palabras: `Juan Perez` / `Perez Juan`

---

## Estructura recomendada del proyecto

```text
comparador_carpetas_google_sheet/
├── .venv/
├── revisar_carpetas.py
├── borrar_carpetas_con_minutos.py
├── minutos.py
├── salida_excel.py
├── probar_google_sheet.py
├── config.example.json
├── config.json
├── service_account.json
├── requirements.txt
├── README.md
├── .gitignore
└── sedes/
    ├── TOMOGRAFIAS COLONIA/
    └── TOMOGRAFIAS DURAZNO/
```

> **Importante:** `service_account.json` contiene una credencial privada. No debe subirse a GitHub, enviarse por correo ni compartirse por mensajería.

> `config.json` contiene la configuración local de cada equipo. Se usa para no tener que editar el script y tampoco debe subirse al repositorio.

---

# Requisitos

- Python 3.10 o superior recomendado.
- Acceso a la Google Sheet que se consultará.
- Una cuenta de Google para crear un proyecto en Google Cloud.
- Permiso para compartir la Google Sheet con una cuenta de servicio.
- Acceso de lectura al directorio de carpetas que se analizará.

---

# 1. Crear el entorno virtual de Python

## macOS

Desde Terminal, entra a la carpeta del proyecto:

```bash
cd ~/Documents/comparador_carpetas_google_sheet
```

Verifica Python:

```bash
python3 --version
```

Crea el entorno virtual:

```bash
python3 -m venv .venv
```

Actívalo:

```bash
source .venv/bin/activate
```

Cuando se active, la terminal mostrará algo parecido a:

```text
(.venv) usuario@MacBook-Pro comparador_carpetas_google_sheet %
```

Actualiza `pip` e instala las dependencias:

```bash
python -m pip install --upgrade pip
pip install gspread google-auth rapidfuzz openpyxl
```

Guarda las dependencias del proyecto:

```bash
pip freeze > requirements.txt
```

Para salir del entorno virtual:

```bash
deactivate
```

## Windows con PowerShell

Abre PowerShell y entra a la carpeta del proyecto:

```powershell
cd C:\ruta\del\proyecto
```

Verifica Python:

```powershell
python --version
```

Si no funciona:

```powershell
py --version
```

Crea el entorno virtual:

```powershell
python -m venv .venv
```

O:

```powershell
py -m venv .venv
```

Actívalo:

```powershell
.\.venv\Scripts\Activate.ps1
```

Si PowerShell bloquea scripts, ejecuta esto solo para la sesión actual:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Luego actívalo otra vez:

```powershell
.\.venv\Scripts\Activate.ps1
```

Instala dependencias:

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Para salir:

```powershell
deactivate
```

---

# 2. Preparar Google Cloud y Google Sheets

El script usa una **Service Account** de Google Cloud. Es una cuenta técnica que permitirá al programa leer la Google Sheet sin abrir sesión manualmente cada vez.

## 2.1 Obtener el ID de la Google Sheet

Abre la Google Sheet en el navegador.

La URL normalmente tiene esta estructura:

```text
https://docs.google.com/spreadsheets/d/1AbCdEfGhIjKlMnOpQrStUvWxYz1234567890/edit#gid=0
```

El ID es el texto entre:

```text
/spreadsheets/d/
```

y:

```text
/edit
```

En el ejemplo anterior, el ID sería:

```text
1AbCdEfGhIjKlMnOpQrStUvWxYz1234567890
```

Ese valor debe configurarse en `config.json`:

```json
{
  "google_sheet_id": "1AbCdEfGhIjKlMnOpQrStUvWxYz1234567890"
}
```

> El valor `gid=0` no es el ID principal del documento. Identifica una pestaña específica.

---

## 2.2 Crear un proyecto en Google Cloud

1. Entra a Google Cloud Console: `https://console.cloud.google.com/`
2. Inicia sesión con una cuenta que tenga acceso a la Google Sheet.
3. En la parte superior, abre el selector de proyectos.
4. Selecciona **Nuevo proyecto**.
5. Define un nombre, por ejemplo:

   ```text
   Comparador Carpetas Google Sheets
   ```

6. Deja la organización y ubicación predeterminadas, salvo que tu empresa indique otra configuración.
7. Pulsa **Crear**.
8. Espera a que el proyecto se cree y verifica que quede seleccionado en la barra superior.

---

## 2.3 Habilitar Google Sheets API

Con el proyecto correcto seleccionado:

1. Abre el menú lateral.
2. Ve a **APIs y servicios**.
3. Entra a **Biblioteca**.
4. Busca:

   ```text
   Google Sheets API
   ```

5. Abre el resultado llamado **Google Sheets API**.
6. Pulsa **Habilitar**.

Para la versión actual del script, Google Sheets API es suficiente porque solo se necesita leer la hoja.

---

## 2.4 Crear una cuenta de servicio

1. Abre el menú lateral de Google Cloud.
2. Ve a **IAM y administración**.
3. Entra a **Cuentas de servicio**.
4. Pulsa **Crear cuenta de servicio**.
5. Completa los datos:

   - **Nombre:** `comparador-carpetas`
   - **Descripción:** `Lectura de Google Sheets para comparar carpetas de estudios.`

6. Pulsa **Crear y continuar**.
7. En la sección de roles del proyecto, no es necesario agregar roles para este caso.
8. Pulsa **Continuar** y luego **Listo**.

La cuenta de servicio no necesita ser administradora ni editora del proyecto. El acceso a la planilla se otorgará compartiendo específicamente esa Google Sheet con su correo.

---

## 2.5 Crear la clave JSON de la cuenta de servicio

1. En la lista de cuentas de servicio, abre la cuenta creada.
2. Ve a la pestaña **Claves** o **Keys**.
3. Selecciona **Agregar clave**.
4. Elige **Crear clave nueva**.
5. Selecciona el formato **JSON**.
6. Pulsa **Crear**.

El navegador descargará un archivo `.json`. Muévelo a la carpeta del proyecto y renómbralo:

```text
service_account.json
```

Ejemplo:

```text
comparador_carpetas_google_sheet/
├── revisar_carpetas.py
├── config.json
├── service_account.json
└── README.md
```

> **Seguridad:** este archivo contiene una clave privada. Trátalo como una contraseña de alto privilegio.

---

## 2.6 Obtener el correo de la cuenta de servicio

Abre `service_account.json` en un editor de texto.

Busca un campo parecido a este:

```json
"client_email": "comparador-carpetas@mi-proyecto.iam.gserviceaccount.com"
```

Copia el correo completo:

```text
comparador-carpetas@mi-proyecto.iam.gserviceaccount.com
```

Ese correo representa al script.

---

## 2.7 Compartir la Google Sheet con la cuenta de servicio

1. Abre la Google Sheet.
2. Pulsa el botón **Compartir**.
3. En el campo para agregar personas, pega el correo de la cuenta de servicio.
4. Asigna permiso **Lector** o **Viewer**.
5. Pulsa **Enviar**.

No es necesario hacer pública la hoja ni habilitar “cualquier persona con el enlace”.

---

# 3. Estructura esperada de la Google Sheet

El script asume la siguiente configuración:

- Los encabezados están en la **fila 11**.
- Los registros comienzan en la **fila 12**.
- La columna `FECHA` contiene el día y mes, por ejemplo `1/6`.
- La columna `NOMBRE` contiene el nombre de la persona.
- La columna `MINUTOS INF` indica minutos de informe cuando contiene un entero mayor que cero.

Ejemplo:

| FECHA | NOMBRE | DR. | CEDULA | F. NACIMIENTO | SALIDA | TIPO DE ESTUDIO | OBSERVACIONES | ENVIO A... | TECNICO | MINUTOS INF |
|---|---|---|---|---|---|---|---|---|---|---|
| 1/6 | Sofia Araujo | Viviana Lambrechts | 45691787 | 17/05/1994 | mail/medcloud | max mand completa | | soofiaraujo@gmail.com | VALE | 50 |

El script solo necesita estas tres columnas:

```text
FECHA
NOMBRE
MINUTOS INF
```

Las demás pueden existir y no afectan el resultado.

---

# 4. Configurar el proyecto

No es necesario editar `revisar_carpetas.py`. La configuración se guarda en `config.json`.

Copia la plantilla:

## macOS o Linux

```bash
cp config.example.json config.json
```

## Windows PowerShell

```powershell
Copy-Item config.example.json config.json
```

Luego abre `config.json` y completa los valores:

```json
{
  "directorio_principal": "C:\\Ruta\\Del\\Directorio\\sedes",
  "archivo_credenciales": "service_account.json",
  "google_sheet_id": "REEMPLAZAR_POR_EL_ID_DEL_GOOGLE_SHEET",
  "nombre_hoja": "Hoja 1",
  "fila_encabezados": 11,
  "fila_inicial_datos": 12,
  "archivo_salida": "resultado_comparacion_carpetas.xlsx",
  "umbral_coincidencia_probable": 90,
  "umbral_revision_manual": 75
}
```

## Configuración para probar desde macOS

Para una prueba local en Mac puedes usar:

```json
{
  "directorio_principal": "~/Documents/prueba_carpetas_google_sheet/sedes"
}
```

## Configuración para Windows

Cuando se ejecute en Windows, cambia la ruta por la ubicación real:

```json
{
  "directorio_principal": "C:\\Estudios\\Tomografias"
}
```

En JSON, las barras invertidas de Windows deben escribirse dobles: `\\`.

Si `archivo_credenciales` es una ruta relativa, se interpreta desde la carpeta del proyecto. Si `archivo_salida` es solo un nombre de archivo, el Excel se crea dentro de `directorio_principal`.

Las configuraciones existentes que todavía terminen en `.csv` se convierten automáticamente a `.xlsx` al ejecutar el script.

---

# 5. Cómo se comparan los nombres

El script transforma los nombres antes de compararlos:

- Convierte a minúsculas.
- Elimina tildes.
- Convierte `_` y `-` en espacios.
- Elimina puntuación.
- Elimina espacios repetidos.
- Ordena las palabras para tolerar cambios de posición.

Ejemplos que deben coincidir:

```text
Sofia_Araujo        ↔ Sofia Araujo
Sofia-Araujo        ↔ SOFIA ARAUJO
José González       ↔ Jose Gonzalez
Juan Perez          ↔ Perez Juan
Maria_Eugenia_Rodriguez ↔ Rodriguez Maria Eugenia
```

Además de la coincidencia exacta tras normalizar, se calcula un porcentaje de similitud.

Estados esperados:

| Estado | Interpretación |
|---|---|
| `Coincidencia exacta` | Los nombres son iguales después de normalizar y ordenar las palabras. |
| `Coincidencia probable` | Similitud alta, por defecto igual o superior a 90%. |
| `Posible coincidencia - revisar` | Similitud entre 75% y 89.99%; requiere verificación humana. |
| `No encontrado` | Similitud inferior a 75%. |
| `Sin carpeta coincidente` | Registro de Google Sheets sin minutos válidos que se incluye aunque no exista una carpeta asociada. |

Los umbrales se pueden ajustar en `config.json`:

```json
{
  "umbral_coincidencia_probable": 90,
  "umbral_revision_manual": 75
}
```

> La similitud de nombres no es una identificación definitiva. Dos personas distintas pueden compartir nombres similares, y una misma persona puede aparecer varias veces en la hoja. Revisa siempre los resultados que no sean coincidencias exactas.

---

# 6. Ejecutar una prueba de conexión a Google Sheets

Antes de ejecutar el script principal, es recomendable probar la conexión. El archivo `probar_google_sheet.py` ya está incluido y usa los mismos valores de `config.json`.

Ejecuta:

```bash
python probar_google_sheet.py
```

Resultado esperado:

```text
Conexión correcta.
Título del documento: Tomografías
Título de la pestaña: Hoja 1
['FECHA', 'NOMBRE', 'DR.', 'CEDULA', ...]
['1/6', 'Sofia Araujo', 'Viviana Lambrechts', ...]
```

---

# 7. Ejecutar el script principal

Con el entorno virtual activado:

## macOS

```bash
python revisar_carpetas.py
```

## Windows

```powershell
python .\revisar_carpetas.py
```

El archivo final se crea según el valor `archivo_salida` de `config.json`. Si es solo un nombre de archivo, se guarda dentro de `directorio_principal`:

```text
resultado_comparacion_carpetas.xlsx
```

---

# 7.1 Retirar carpetas que ya tienen minutos

El script `borrar_carpetas_con_minutos.py` busca filas cuya columna `MINUTOS INF` contiene un entero mayor que cero y las compara con las carpetas locales.

Una celda cuenta como minutos válidos si contiene solamente dígitos y su valor es mayor que cero. Por ejemplo:

| Valor | ¿Tiene minutos? |
|---|---|
| `50` | Sí |
| `001` | Sí |
| `0` | No |
| `12.5` | No |
| `pendiente` | No |
| `-5` | No |

Ejecuta:

```bash
python borrar_carpetas_con_minutos.py
```

En Windows también puedes usar:

```powershell
python .\borrar_carpetas_con_minutos.py
```

Antes de realizar cambios, el script muestra:

- Número de fila de Google Sheets.
- Nombre y minutos registrados.
- Tipo y porcentaje de coincidencia.
- Ruta completa de la carpeta local.
- Coincidencias ambiguas y filas que no tienen carpeta.

Solo se ofrecen coincidencias exactas o probables según `umbral_coincidencia_probable`. Si una fila coincide con varias carpetas, o una carpeta coincide con varias filas, el caso se omite para revisión manual.

Para continuar debes escribir exactamente:

```text
BORRAR
```

Las carpetas confirmadas, junto con todo su contenido, se borran definitivamente sin pasar por la Papelera del sistema; no se borran filas de Google Sheets. Esta acción es irreversible, por lo que conviene revisar cuidadosamente la vista previa antes de escribir `BORRAR`.

La cuenta de servicio solo necesita permiso de lectura sobre la Google Sheet para ambos scripts.

---

# 8. Hojas y columnas del Excel generado

El libro contiene estas hojas:

| Hoja | Contenido |
|---|---|
| `Salida actual` | Todos los resultados que anteriormente se incluían en el CSV. |
| `Con minutos` | Solo los resultados cuyo `MINUTOS INF` es un entero mayor que cero. |
| `Carpetas no encontradas` | Carpetas locales con estado `No encontrado` o `Sin datos en Google Sheet`. Las coincidencias para revisar permanecen únicamente en la salida general. |
| `Sin minutos ni carpeta` | Filas de Google Sheets sin minutos válidos para las cuales no se encontró una carpeta coincidente. |

Las tres hojas conservan las mismas columnas:

| Columna | Descripción |
|---|---|
| `Sede` | Nombre de la carpeta sede. |
| `NombreOriginalCarpeta` | Nombre original de la carpeta encontrada. |
| `NombreNormalizadoCarpeta` | Nombre transformado para comparación. |
| `NombreOrdenadoCarpeta` | Palabras del nombre ordenadas alfabéticamente. |
| `RutaCompleta` | Ruta local completa de la carpeta. |
| `EstaVacia` | `Sí` cuando no tiene archivos ni subcarpetas. |
| `CantidadItems` | Total de elementos directos dentro de la carpeta. |
| `CantidadArchivos` | Total de archivos directos. |
| `CantidadSubcarpetas` | Total de subcarpetas directas. |
| `EstadoComparacion` | Resultado de la comparación contra Google Sheets. |
| `PorcentajeSimilitud` | Nivel de similitud encontrado. |
| `FilaGoogleSheet` | Número de fila del registro encontrado en Google Sheets. |
| `FechaOriginalGoogleSheet` | Fecha vigente tomada de `FECHA`; si la fila no tiene fecha, usa la última fecha anterior de la hoja. |
| `NombreEncontradoGoogleSheet` | Nombre original encontrado en la hoja. |
| `TieneMinutosInf` | `Sí` si `MINUTOS INF` contiene un entero mayor que cero. |
| `ValorMinutosInf` | Valor original de `MINUTOS INF`. |

Cada hoja incluye encabezados destacados, filtros, la primera fila congelada, anchos de columna ajustados y colores para facilitar la revisión de los estados.

---

# 9. Crear una estructura de prueba en macOS

Para probar el proceso sin tocar carpetas reales, crea el archivo `crear_estructura_prueba.sh`:

```bash
#!/bin/bash

BASE_DIR="$HOME/Documents/prueba_carpetas_google_sheet/sedes"

mkdir -p "$BASE_DIR/TOMOGRAFIAS COLONIA"
mkdir -p "$BASE_DIR/TOMOGRAFIAS DURAZNO"
mkdir -p "$BASE_DIR/TOMOGRAFIAS NUEVO CENTRO"

mkdir -p "$BASE_DIR/TOMOGRAFIAS COLONIA/Sofia_Araujo"
touch "$BASE_DIR/TOMOGRAFIAS COLONIA/Sofia_Araujo/estudio_01.dcm"

mkdir -p "$BASE_DIR/TOMOGRAFIAS COLONIA/Elena-Reolon"
touch "$BASE_DIR/TOMOGRAFIAS COLONIA/Elena-Reolon/estudio_01.dcm"

mkdir -p "$BASE_DIR/TOMOGRAFIAS COLONIA/Alma Ruiz"

mkdir -p "$BASE_DIR/TOMOGRAFIAS DURAZNO/Perez_Juan"
touch "$BASE_DIR/TOMOGRAFIAS DURAZNO/Perez_Juan/informe.pdf"

mkdir -p "$BASE_DIR/TOMOGRAFIAS DURAZNO/RODRIGUEZ__MARIA_EUGENIA"
touch "$BASE_DIR/TOMOGRAFIAS DURAZNO/RODRIGUEZ__MARIA_EUGENIA/archivo.pdf"

mkdir -p "$BASE_DIR/TOMOGRAFIAS NUEVO CENTRO/Persona No Registrada"
touch "$BASE_DIR/TOMOGRAFIAS NUEVO CENTRO/Persona No Registrada/archivo.txt"

echo "Estructura creada en: $BASE_DIR"
```

Hazlo ejecutable:

```bash
chmod +x crear_estructura_prueba.sh
```

Ejecuta:

```bash
./crear_estructura_prueba.sh
```

Para revisar el contenido:

```bash
find "$HOME/Documents/prueba_carpetas_google_sheet/sedes" -maxdepth 3 -print
```

---

# 10. Archivo `.gitignore`

Crea un archivo llamado `.gitignore` en la raíz del proyecto con este contenido:

```gitignore
.venv/
__pycache__/
*.pyc

# Credenciales privadas de Google Cloud
service_account.json

# Resultados generados
resultado_comparacion_carpetas.xlsx
```

Nunca subas el archivo `service_account.json` a un repositorio.

---

# 11. Errores frecuentes

## `SpreadsheetNotFound`

Causas comunes:

- El ID de Google Sheet está mal.
- La hoja no fue compartida con el correo de la cuenta de servicio.
- Se está usando un archivo `service_account.json` de otro proyecto.

Solución:

1. Revisa el ID.
2. Abre la Google Sheet.
3. Pulsa **Compartir**.
4. Verifica que el valor de `client_email` de `service_account.json` tenga permiso de **Lector**.

## `WorksheetNotFound`

El ID del documento es correcto, pero el valor de:

```json
{
  "nombre_hoja": "..."
}
```

no coincide con el nombre visible de la pestaña inferior.

Copia ese nombre exactamente, incluyendo espacios, tildes y mayúsculas.

## `FileNotFoundError: service_account.json`

El script no encuentra el archivo de credenciales.

Comprueba que:

- `service_account.json` esté en la carpeta desde la cual ejecutas el script; o
- `archivo_credenciales` tenga una ruta correcta en `config.json`.

Ejemplo para macOS:

```json
{
  "archivo_credenciales": "~/Documents/comparador_carpetas_google_sheet/service_account.json"
}
```

Ejemplo para Windows:

```json
{
  "archivo_credenciales": "C:\\ComparadorCarpetas\\service_account.json"
}
```

## `ModuleNotFoundError`

El entorno virtual no está activo o las dependencias no fueron instaladas.

Activa el entorno y ejecuta:

```bash
pip install -r requirements.txt
```

## Error de permisos al revisar carpetas

El usuario que ejecuta el script debe tener permiso de lectura sobre las carpetas de sedes y las carpetas de personas.

En Windows, asegúrate de ejecutar el script con un usuario que pueda acceder a la unidad o carpeta compartida correspondiente.

---

# Seguridad y buenas prácticas

- Mantén el Google Sheet privado.
- Comparte la hoja solo con la cuenta de servicio y con los usuarios necesarios.
- Otorga permiso de **Lector** a la cuenta de servicio mientras el script solo consulte datos.
- Protege `service_account.json`.
- Evita comparar o consolidar resultados automáticamente cuando la coincidencia sea “probable” o “para revisar”.
- Conserva el Excel como reporte de auditoría para validar resultados.
- Si en el futuro existe un identificador único en carpetas o Google Sheets, como cédula, número de historia clínica o ID de paciente, úsalo como clave principal. El nombre debe quedar como dato complementario.

---

# Ejecución cotidiana

## macOS

```bash
cd ~/Documents/comparador_carpetas_google_sheet
source .venv/bin/activate
python revisar_carpetas.py
```

## Windows

```powershell
cd C:\ruta\del\proyecto
.\.venv\Scripts\Activate.ps1
python .\revisar_carpetas.py
```

Al finalizar, abre `resultado_comparacion_carpetas.xlsx`. La hoja `Salida actual` permite filtrar especialmente por:

- `EstadoComparacion`
- `PorcentajeSimilitud`
- `EstaVacia`
- `TieneMinutosInf`
- `Sede`
