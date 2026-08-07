param(
    [Parameter(Mandatory = $true)]
    [string]$InputPath,

    [string]$OutputDirectory = (Join-Path $PSScriptRoot 'dados_separados'),

    [string]$Participant = '00',

    [double]$MinimumGapSeconds = 2.0
)

$ErrorActionPreference = 'Stop'
$culture = [Globalization.CultureInfo]::InvariantCulture
$timeFormat = 'HH:mm:ss:fff'
$records = [System.Collections.Generic.List[object]]::new()

$lineNumber = 0
Get-Content -LiteralPath $InputPath | ForEach-Object {
    $lineNumber++
    $match = [regex]::Match($_, '^\s*([^,]+),\s*([^,]+),\s*(\d{2}:\d{2}:\d{2}:\d{3})\s*$')
    if ($match.Success) {
        $records.Add([pscustomobject]@{
            Line = $lineNumber
            Text = $_
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

for ($task = 1; $task -le 6; $task++) {
    $startIndex = $selectedGaps[$task - 1].AfterIndex
    $endIndex = $selectedGaps[$task].BeforeIndex
    $name = 'P{0}T{1:D2}.txt' -f $Participant, $task
    $outputPath = Join-Path $OutputDirectory $name
    $writer = [IO.StreamWriter]::new($outputPath, $false, $utf8WithoutBom)
    try {
        $writer.WriteLine('x,y,tempo')
        for ($index = $startIndex; $index -le $endIndex; $index++) {
            $writer.WriteLine($records[$index].Text)
        }
    }
    finally {
        $writer.Dispose()
    }
}

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
