import gspread
from google.oauth2.service_account import Credentials

from revisar_carpetas import (
    ARCHIVO_CREDENCIALES,
    FILA_ENCABEZADOS,
    GOOGLE_SHEET_ID,
    NOMBRE_HOJA,
)

scopes = [
    "https://www.googleapis.com/auth/spreadsheets.readonly"
]

credentials = Credentials.from_service_account_file(
    ARCHIVO_CREDENCIALES,
    scopes=scopes
)

cliente = gspread.authorize(credentials)

documento = cliente.open_by_key(GOOGLE_SHEET_ID)
hoja = documento.worksheet(NOMBRE_HOJA)

print("Conexión correcta.")
print("Título del documento:", documento.title)
print("Título de la pestaña:", hoja.title)

for fila in hoja.get(f"A{FILA_ENCABEZADOS}:K{FILA_ENCABEZADOS + 4}"):
    print(fila)
