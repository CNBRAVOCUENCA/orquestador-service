param(
    [Parameter(Mandatory = $true)]
    [string]$PdfPath,

    [Parameter(Mandatory = $true)]
    [string]$Name
)

$ErrorActionPreference = "Stop"
$vegetaDirectory = Join-Path $PSScriptRoot "infra\vegeta"
if (-not (Test-Path -LiteralPath $vegetaDirectory -PathType Container)) {
    throw "No se encontro la carpeta infra\vegeta. Ejecuta este script desde el proyecto principal."
}

if (-not (Test-Path -LiteralPath $PdfPath -PathType Leaf)) {
    throw "No se encontro el archivo: $PdfPath"
}

$pdfFullPath = (Resolve-Path -LiteralPath $PdfPath).Path
if ([IO.Path]::GetExtension($pdfFullPath) -ine ".pdf") {
    throw "El archivo debe tener extension .pdf."
}

$responsePath = [IO.Path]::GetTempFileName()
try {
    $statusCode = & curl.exe `
        --silent `
        --show-error `
        --output $responsePath `
        --write-out "%{http_code}" `
        -H "Host: documentos.localhost" `
        --form-string "name=$Name" `
        -F "file=@${pdfFullPath};type=application/pdf" `
        "http://localhost/api/v1/documents"

    if ($LASTEXITCODE -ne 0) {
        throw "No se pudo contactar documentos-service. Comprueba que el stack este activo."
    }

    $responseText = [IO.File]::ReadAllText($responsePath)
    if ([int]$statusCode -eq 409) {
        throw "El PDF ya existe (HTTP 409). No lo subas otra vez; usa su document_id anterior."
    }
    if ([int]$statusCode -lt 200 -or [int]$statusCode -ge 300) {
        throw "La subida fallo con HTTP $statusCode. Respuesta: $responseText"
    }

    try {
        $response = $responseText | ConvertFrom-Json
    }
    catch {
        throw "documentos-service devolvio una respuesta JSON invalida."
    }

    if ($null -eq $response.id) {
        throw "La respuesta de documentos-service no contiene el ID del documento."
    }

    $documentId = [int]$response.id
    $body = @{ document_id = $documentId } | ConvertTo-Json -Compress
    [IO.File]::WriteAllText((Join-Path $vegetaDirectory "document-id.txt"), [string]$documentId, [Text.Encoding]::ASCII)
    [IO.File]::WriteAllText((Join-Path $vegetaDirectory "extractor-body.json"), $body, [Text.Encoding]::ASCII)

    Write-Host "PDF subido correctamente. document_id=$documentId"
}
finally {
    Remove-Item -LiteralPath $responsePath -Force -ErrorAction SilentlyContinue
}
