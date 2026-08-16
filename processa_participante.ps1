param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$Participant,

    [string]$PythonExecutable = 'python',

    [double]$MinimumGapSeconds = 2.0
)

$ErrorActionPreference = 'Stop'
$participantNumber = $Participant -replace '^P', ''
if ($participantNumber -notmatch '^\d+$') {
    throw 'Participante invalido. Use 00, 01, 02... ou P00, P01, P02...'
}
$participantLabel = "P$participantNumber"
$documentsDirectory = [Environment]::GetFolderPath('MyDocuments')
$demoDirectory = Join-Path $documentsDirectory 'demo'
$collectionDirectory = Join-Path (Join-Path $demoDirectory 'coletas') $participantLabel
$EyeTrackerFile = Join-Path $collectionDirectory "data$participantLabel.txt"
$ExperimentJson = Join-Path $collectionDirectory "resultado$participantLabel.json"
$DataDirectory = Join-Path $demoDirectory 'data'
$ImagesDirectory = Join-Path $demoDirectory 'telas'
$GraphsDirectory = Join-Path $demoDirectory 'graficos'
$participantDirectory = Join-Path $DataDirectory $participantLabel
$taskSummaryPath = Join-Path $participantDirectory 'resumo_tarefas.csv'
$splitScript = Join-Path $PSScriptRoot 'split_eyetracker.ps1'
$mainScript = Join-Path $PSScriptRoot 'scripts\main_script_adap.py'

New-Item -ItemType Directory -Path $participantDirectory -Force | Out-Null

if (-not (Test-Path -LiteralPath $EyeTrackerFile -PathType Leaf)) {
    throw "Arquivo do eye tracker nao encontrado: $EyeTrackerFile"
}
if (-not (Test-Path -LiteralPath $ExperimentJson -PathType Leaf)) {
    throw "JSON do experimento nao encontrado: $ExperimentJson"
}

& $splitScript `
    -InputPath $EyeTrackerFile `
    -ExperimentJson $ExperimentJson `
    -OutputDirectory $participantDirectory `
    -Participant $participantLabel `
    -MinimumGapSeconds $MinimumGapSeconds

& $PythonExecutable $mainScript `
    --participant $participantLabel `
    --data-dir $DataDirectory `
    --images-dir $ImagesDirectory `
    --graphs-dir $GraphsDirectory `
    --task-summary $taskSummaryPath

if ($LASTEXITCODE -ne 0) {
    throw "A geracao dos graficos falhou com codigo $LASTEXITCODE."
}

Write-Host "Processamento concluido para $participantLabel."
