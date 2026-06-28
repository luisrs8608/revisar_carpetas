# Directorio principal que contiene las carpetas de sedes
$directorioPrincipal = "C:\Ruta\Del\Directorio"

# Archivo CSV que se generará dentro del directorio principal
$archivoSalida = Join-Path $directorioPrincipal "listado_personas_por_sede.csv"

$resultado = foreach ($sede in Get-ChildItem -Path $directorioPrincipal -Directory) {

    # Recorrer las carpetas hijas de cada sede
    foreach ($carpetaHija in Get-ChildItem -Path $sede.FullName -Directory) {

        # Nombre original de la carpeta
        $nombreOriginal = $carpetaHija.Name

        # Normalizar separadores:
        # "_" y "-" pasan a ser espacios.
        # Luego se eliminan espacios repetidos al inicio, medio o final.
        $nombreNormalizado = $nombreOriginal `
            -replace '[_-]+', ' ' `
            -replace '\s+', ' '

        $nombreNormalizado = $nombreNormalizado.Trim()

        # Contenido directo de la carpeta: archivos y subcarpetas
        $contenido = Get-ChildItem -Path $carpetaHija.FullName -Force

        # Contar archivos y subcarpetas por separado
        $cantidadArchivos = ($contenido | Where-Object { -not $_.PSIsContainer }).Count
        $cantidadSubcarpetas = ($contenido | Where-Object { $_.PSIsContainer }).Count

        [PSCustomObject]@{
            Sede                = $sede.Name
            NombreOriginal      = $nombreOriginal
            NombreNormalizado   = $nombreNormalizado
            RutaCompleta        = $carpetaHija.FullName
            EstaVacia           = if ($contenido.Count -eq 0) { "Sí" } else { "No" }
            CantidadItems       = $contenido.Count
            CantidadArchivos    = $cantidadArchivos
            CantidadSubcarpetas = $cantidadSubcarpetas
        }
    }
}

$resultado |
    Sort-Object Sede, NombreNormalizado |
    Export-Csv -Path $archivoSalida -NoTypeInformation -Encoding UTF8

Write-Host "Archivo generado en: $archivoSalida"