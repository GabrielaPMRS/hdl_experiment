param(
    [Parameter(Mandatory = $true)]
    [string]$InputPath,

    [Parameter(Mandatory = $true)]
    [string]$ExperimentJson,

    [string]$OutputDirectory = (Join-Path $PSScriptRoot 'dados_separados'),

    [string]$Participant = '00',

    [double]$MinimumGapSeconds = 2.0
)

$ErrorActionPreference = 'Stop'
$culture = [Globalization.CultureInfo]::InvariantCulture
$timeFormat = 'HH:mm:ss:fff'
$records = [System.Collections.Generic.List[object]]::new()
$participantCode = if ($Participant -match '^P(.+)$') { $Matches[1] } else { $Participant }
$participantLabel = "P$participantCode"

if (-not (Test-Path -LiteralPath $ExperimentJson -PathType Leaf)) {
    throw "JSON do experimento nao encontrado: $ExperimentJson"
}

$experiment = Get-Content -LiteralPath $ExperimentJson -Raw | ConvertFrom-Json
if ($experiment -is [array]) {
    if ($experiment.Count -ne 1) {
        throw 'O JSON deve conter exatamente uma sessao de participante.'
    }
    $experiment = $experiment[0]
}

$questions = @($experiment.perguntas | Sort-Object { [int]$_.ordemExecucao })
if ($questions.Count -ne 6) {
    throw "O JSON possui $($questions.Count) tarefas concluidas; eram esperadas 6."
}

$experimentVersion = ([string]$experiment.versaoExperimento).ToLowerInvariant()
if ($experimentVersion -notin @('lambda', 'omega')) {
    throw "Versao do experimento invalida no JSON: $experimentVersion"
}

$executionOrder = [System.Collections.Generic.List[object]]::new()
for ($position = 1; $position -le 6; $position++) {
    $question = $questions[$position - 1]
    if ([int]$question.ordemExecucao -ne $position) {
        throw "Ordem de execucao invalida no JSON: esperava $position e encontrou $($question.ordemExecucao)."
    }
    if ([string]$question.codigoId -notmatch '(\d+)$') {
        throw "codigoId invalido no JSON: $($question.codigoId)"
    }
    $realTask = 'T{0:D2}' -f [int]$Matches[1]
    $executionOrder.Add([pscustomobject]@{
        Participante = $participantLabel
        VersaoExperimento = $experimentVersion
        PosicaoExecucao = $position
        Arquivo = ('{0}T{1:D2} 1.txt' -f $participantLabel, $position)
        TarefaReal = $realTask
        CodigoId = [string]$question.codigoId
        SegundosAplicacao = [double]$question.segundos
        Tentativas = [int]$question.tentativas
        ParticipanteIdJson = [string]$experiment.participanteId
    })
}

if (($executionOrder.TarefaReal | Sort-Object -Unique).Count -ne 6) {
    throw 'O JSON contem tarefas repetidas ou ausentes.'
}

$lineNumber = 0
Get-Content -LiteralPath $InputPath | ForEach-Object {
    $lineNumber++
    $match = [regex]::Match($_, '^\s*([^,]+),\s*([^,]+),\s*(\d{2}:\d{2}:\d{2}:\d{3})\s*$')
    if ($match.Success) {
        $records.Add([pscustomobject]@{
            Line = $lineNumber
            Text = $_
            X = [double]::Parse($match.Groups[1].Value.Trim(), $culture)
            Y = [double]::Parse($match.Groups[2].Value.Trim(), $culture)
            Time = [datetime]::ParseExact($match.Groups[3].Value, $timeFormat, $culture)
        })
    }
}

$gaps = [System.Collections.Generic.List[object]]::new()
for ($index = 1; $index -lt $records.Count; $index++) {
    $seconds = ($records[$index].Time - $records[$index - 1].Time).TotalSeconds
    if ($seconds -lt 0) { $seconds += 86400 }
    if ($seconds -ge $MinimumGapSeconds) {
        $gaps.Add([pscustomobject]@{
            BeforeIndex = $index - 1
            AfterIndex = $index
            Seconds = $seconds
        })
    }
}

if ($gaps.Count -lt 7) {
    throw "Foram encontrados apenas $($gaps.Count) gaps; são necessários 7 para delimitar 6 tarefas."
}

# A primeira sequência de 7 gaps delimita as 6 tarefas da primeira gravação completa.
$selectedGaps = $gaps | Select-Object -First 7
New-Item -ItemType Directory -Path $OutputDirectory -Force | Out-Null
$utf8WithoutBom = [Text.UTF8Encoding]::new($false)
$cleaningSummary = [System.Collections.Generic.List[object]]::new()

for ($task = 1; $task -le 6; $task++) {
    $startIndex = $selectedGaps[$task - 1].AfterIndex
    $endIndex = $selectedGaps[$task].BeforeIndex
    $name = '{0}T{1:D2} 1.txt' -f $participantLabel, $task
    $outputPath = Join-Path $OutputDirectory $name
    $writer = [IO.StreamWriter]::new($outputPath, $false, $utf8WithoutBom)
    $kept = 0
    $removedNegativeX = 0
    $removedNegativeY = 0
    $removedXAtOrAbove820 = 0
    try {
        $writer.WriteLine('x,y,tempo')
        for ($index = $startIndex; $index -le $endIndex; $index++) {
            $record = $records[$index]
            if ($record.X -lt 0) {
                $removedNegativeX++
                continue
            }
            if ($record.Y -lt 0) {
                $removedNegativeY++
                continue
            }
            if ($record.X -ge 820) {
                $removedXAtOrAbove820++
                continue
            }
            $writer.WriteLine($record.Text)
            $kept++
        }
    }
    finally {
        $writer.Dispose()
    }
    $cleaningSummary.Add([pscustomobject]@{
        File = $name
        OriginalRows = $endIndex - $startIndex + 1
        KeptRows = $kept
        RemovedNegativeX = $removedNegativeX
        RemovedNegativeY = $removedNegativeY
        RemovedXAtOrAbove820 = $removedXAtOrAbove820
    })
}

$cleaningSummary | Export-Csv -LiteralPath (Join-Path $OutputDirectory 'resumo_limpeza.csv') -NoTypeInformation -Encoding utf8
$executionOrder | Export-Csv -LiteralPath (Join-Path $OutputDirectory 'ordem_tarefas.csv') -NoTypeInformation -Encoding utf8

$selectedGaps | ForEach-Object {
    $before = $records[$_.BeforeIndex]
    $after = $records[$_.AfterIndex]
    [pscustomobject]@{
        BeforeLine = $before.Line
        BeforeTime = $before.Time.ToString($timeFormat)
        AfterLine = $after.Line
        AfterTime = $after.Time.ToString($timeFormat)
        GapSeconds = [math]::Round($_.Seconds, 3)
    }
} | Export-Csv -LiteralPath (Join-Path $OutputDirectory 'limites_gaps.csv') -NoTypeInformation -Encoding utf8
