param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$Participant,

    [string]$BrowserExecutable
)

$ErrorActionPreference = 'Stop'

$participantNumberText = $Participant -replace '^P', ''
if ($participantNumberText -notmatch '^\d+$') {
    throw 'Participante invalido. Use 00, 01, 02... ou P00, P01, P02...'
}

$participantNumber = [int]$participantNumberText
$participantLabel = 'P{0:D2}' -f $participantNumber
$configPath = Join-Path $PSScriptRoot 'config\condicoes_participantes.json'
$config = Get-Content -LiteralPath $configPath -Raw | ConvertFrom-Json

if ($config.regra -ne 'paridade') {
    throw "Regra de atribuicao desconhecida: $($config.regra)"
}

$experimentVersion = if ($participantNumber % 2 -eq 0) {
    [string]$config.par
} else {
    [string]$config.impar
}

$applicationDirectory = switch ($experimentVersion) {
    'lambda' { Join-Path $PSScriptRoot 'lambda-smell-pares' }
    'omega'  { Join-Path $PSScriptRoot 'omega-NoSmell-impares' }
    default  { throw "Versao de experimento desconhecida: $experimentVersion" }
}

$trackerExecutable = 'C:\TobiiEyeTracker4CDataStream-1-master\TobiiEyeTracker4CDataStream2\bin\Debug\TobiiEyeTracker4CDataStream.exe'
if (-not (Test-Path -LiteralPath $trackerExecutable -PathType Leaf)) {
    throw "Executavel do eye tracker nao encontrado: $trackerExecutable"
}

$documentsDirectory = [Environment]::GetFolderPath('MyDocuments')
$demoDirectory = Join-Path $documentsDirectory 'demo'
$collectionsDirectory = Join-Path $demoDirectory 'coletas'
$screensDirectory = Join-Path $demoDirectory 'telas'
$lambdaScreensDirectory = Join-Path $screensDirectory 'lambda'
$omegaScreensDirectory = Join-Path $screensDirectory 'omega'
$participantDirectory = Join-Path $collectionsDirectory $participantLabel
$eyeTrackerFile = Join-Path $participantDirectory "data$participantLabel.txt"
$resultFile = Join-Path $participantDirectory "resultado$participantLabel.json"
$applicationPath = Join-Path $applicationDirectory 'index.html'

New-Item -ItemType Directory -Path $participantDirectory -Force | Out-Null
New-Item -ItemType Directory -Path $lambdaScreensDirectory -Force | Out-Null
New-Item -ItemType Directory -Path $omegaScreensDirectory -Force | Out-Null

if (Test-Path -LiteralPath $eyeTrackerFile) {
    throw "A coleta deste participante ja existe: $eyeTrackerFile"
}

if (Test-Path -LiteralPath $resultFile) {
    throw "O resultado deste participante ja existe: $resultFile"
}

$trackerArguments = @(
    $participantLabel,
    ('"{0}"' -f $collectionsDirectory)
)

$trackerProcess = Start-Process `
    -FilePath $trackerExecutable `
    -ArgumentList $trackerArguments `
    -PassThru

Start-Sleep -Milliseconds 750
$trackerProcess.Refresh()
if ($trackerProcess.HasExited) {
    throw "O coletor do eye tracker encerrou antes de a aplicacao ser aberta. Codigo: $($trackerProcess.ExitCode)"
}

$applicationUri = ([Uri]$applicationPath).AbsoluteUri
$applicationUri += '?participante=' + [Uri]::EscapeDataString($participantLabel)

if (-not $BrowserExecutable) {
    $browserCandidates = @(
        "$env:ProgramFiles\Google\Chrome\Application\chrome.exe",
        "${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe",
        "$env:LOCALAPPDATA\Google\Chrome\Application\chrome.exe",
        "$env:ProgramFiles\Microsoft\Edge\Application\msedge.exe",
        "${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe",
        "$env:LOCALAPPDATA\Microsoft\Edge\Application\msedge.exe"
    )
    $BrowserExecutable = $browserCandidates |
        Where-Object { $_ -and (Test-Path -LiteralPath $_ -PathType Leaf) } |
        Select-Object -First 1
}

if (-not $BrowserExecutable -or -not (Test-Path -LiteralPath $BrowserExecutable -PathType Leaf)) {
    throw 'Chrome ou Edge nao encontrado. Informe o navegador com -BrowserExecutable.'
}

$browserProfilesDirectory = Join-Path $demoDirectory 'perfis_navegador'
$browserProfileDirectory = Join-Path $browserProfilesDirectory $participantLabel
$defaultBrowserProfileDirectory = Join-Path $browserProfileDirectory 'Default'
$browserPreferencesPath = Join-Path $defaultBrowserProfileDirectory 'Preferences'
New-Item -ItemType Directory -Path $defaultBrowserProfileDirectory -Force | Out-Null

$browserPreferences = @{
    download = @{
        default_directory = $participantDirectory
        directory_upgrade = $true
        prompt_for_download = $false
    }
    profile = @{
        default_content_setting_values = @{
            automatic_downloads = 1
        }
    }
} | ConvertTo-Json -Depth 6

[IO.File]::WriteAllText(
    $browserPreferencesPath,
    $browserPreferences,
    [Text.UTF8Encoding]::new($false)
)

Start-Process `
    -FilePath $BrowserExecutable `
    -ArgumentList @(
        ('--user-data-dir="{0}"' -f $browserProfileDirectory),
        '--no-first-run',
        '--no-default-browser-check',
        '--new-window',
        ('"{0}"' -f $applicationUri)
    )

Write-Host ''
Write-Host "Participante: $participantLabel"
Write-Host "Versao: $experimentVersion"
Write-Host "Eye tracker: $eyeTrackerFile"
Write-Host "Navegador: $BrowserExecutable"
Write-Host 'A aplicacao foi aberta no navegador.'
Write-Host "O JSON sera salvo automaticamente em: $resultFile"
Write-Host 'Ao terminar o experimento, pressione uma tecla na janela do eye tracker para encerrar a coleta.'
