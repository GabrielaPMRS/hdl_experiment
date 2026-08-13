param(
    [Parameter(Mandatory = $true)]
    [string]$EyeTrackerFile,

    [Parameter(Mandatory = $true)]
    [string]$ExperimentJson,

    [Parameter(Mandatory = $true)]
    [string]$Participant,

    [Parameter(Mandatory = $true)]
    [string]$DataDirectory,

    [Parameter(Mandatory = $true)]
    [string]$ImagesDirectory,

    [Parameter(Mandatory = $true)]
    [string]$GraphsDirectory,

    [string]$PythonExecutable = 'python',

    [double]$MinimumGapSeconds = 2.0
)

$ErrorActionPreference = 'Stop'
$participantLabel = if ($Participant -match '^P') { $Participant } else { "P$Participant" }
$participantDirectory = Join-Path $DataDirectory $participantLabel
$mappingPath = Join-Path $participantDirectory 'ordem_tarefas.csv'
$splitScript = Join-Path $PSScriptRoot 'split_eyetracker.ps1'
$mainScript = Join-Path $PSScriptRoot 'scripts\main_script_adap.py'

New-Item -ItemType Directory -Path $participantDirectory -Force | Out-Null

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
    --mapping $mappingPath

if ($LASTEXITCODE -ne 0) {
    throw "A geracao dos graficos falhou com codigo $LASTEXITCODE."
}

Write-Host "Processamento concluido para $participantLabel."
