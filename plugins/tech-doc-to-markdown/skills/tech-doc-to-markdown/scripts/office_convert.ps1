<#
.SYNOPSIS
Convert DOC, DOCX, RTF or ODT to PDF or DOCX with Microsoft Word automation (Windows only), with a time limit.

.EXAMPLE
powershell -NoProfile -ExecutionPolicy Bypass -File office_convert.ps1 -InputPath "C:\docs\old manual.doc" -OutDir "C:\scratch" -To pdf

.NOTES
- Opens the source read-only and never modifies it.
- Word automation can hang invisibly when Word is waiting on a first-run, sign-in, activation or repair dialog.
  The conversion therefore runs in a background job; after -TimeoutSec the job is stopped and only the Word
  automation instance started by this script is closed. Then open Word once interactively to clear the dialog,
  or use LibreOffice instead:  soffice --headless --convert-to pdf --outdir <dir> <file>
- Exit codes: 0 success, 1 conversion error, 2 timeout.
#>
param(
    [Parameter(Mandatory = $true)][string]$InputPath,
    [Parameter(Mandatory = $true)][string]$OutDir,
    [ValidateSet('pdf', 'docx')][string]$To = 'pdf',
    [int]$TimeoutSec = 120
)
$ErrorActionPreference = 'Stop'
$source = (Resolve-Path -LiteralPath $InputPath).Path
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$outFull = (Resolve-Path -LiteralPath $OutDir).Path
$target = Join-Path $outFull (([IO.Path]::GetFileNameWithoutExtension($source)) + ".$To")
if ($target -eq $source) { throw "Refusing to overwrite the source file; choose another -OutDir." }
$format = @{ pdf = 17; docx = 16 }[$To]   # wdFormatPDF = 17, wdFormatXMLDocument = 16

$before = @(Get-CimInstance Win32_Process -Filter "Name = 'WINWORD.EXE'" | ForEach-Object ProcessId)
$job = Start-Job -ArgumentList $source, $target, $format -ScriptBlock {
    param($src, $dst, $fmt)
    $ErrorActionPreference = 'Stop'
    $word = New-Object -ComObject Word.Application
    try {
        $word.Visible = $false
        $word.DisplayAlerts = 0
        $doc = $word.Documents.Open($src, $false, $true)   # FileName, ConfirmConversions, ReadOnly
        try { $doc.SaveAs2($dst, $fmt) } finally { $doc.Close($false) }
    } finally {
        $word.Quit()
        [void][Runtime.InteropServices.Marshal]::ReleaseComObject($word)
    }
    $dst
}

if (Wait-Job $job -Timeout $TimeoutSec) {
    try {
        Receive-Job $job -ErrorAction Stop
        Remove-Job $job -Force
        exit 0
    } catch {
        Remove-Job $job -Force
        Write-Error "Word conversion failed: $($_.Exception.Message)"
        exit 1
    }
}

Stop-Job $job
Remove-Job $job -Force
Get-CimInstance Win32_Process -Filter "Name = 'WINWORD.EXE'" |
    Where-Object { $before -notcontains $_.ProcessId -and $_.CommandLine -match '/Automation' } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force -Confirm:$false }
Write-Error ("Word did not respond within $TimeoutSec s. It is probably waiting on a first-run, sign-in, activation " +
    "or repair dialog. Open Word once interactively and close that dialog, or convert with LibreOffice.")
exit 2
