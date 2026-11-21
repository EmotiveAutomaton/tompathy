# Project only the commissioned columns from a local, pinned research copy.
$ErrorActionPreference = 'Stop'
$root = [Environment]::GetEnvironmentVariable('SOUNDING_LINE_DATA_ROOT','User')
if ($root -ne 'C:\Users\abrah\AppData\Local\SoundingLine\DRT1-20261121') { throw 'Local DRT1 root required' }
$manifest = 'E:/EmotiveAutomaton/Projects/SoundingLine/sounding-line/results/phase_2_4_stage_15/WEEK5/DRT1_OPEN_MANIFEST_20261121.json'
if ((Get-FileHash $manifest).Hash -ne 'cc63f8f6ffb5a47845b98b0d754b6412c18b0e6c79ea5badd8466d5589075f6d') { throw 'Manifest changed' }
$entry = (Get-Content $manifest -Raw | ConvertFrom-Json).files | Where-Object path -eq 'open/isear/raw/isear_databank.zip'
$zip = Join-Path $root $entry.path
if ((Get-FileHash $zip).Hash -ne $entry.sha256) { throw 'ISEAR archive changed' }
$out = Join-Path $PSScriptRoot '../.local/person-teacher/cb'
[void][IO.Directory]::CreateDirectory($out)
$db = Join-Path $out 'isear.mdb'
$archive = [IO.Compression.ZipFile]::OpenRead($zip)
try {
    $s = $archive.GetEntry('isear_databank.mdb').Open()
    try {
        if (Test-Path -LiteralPath $db) {
            if ([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($s)) -ne (Get-FileHash $db).Hash) { throw 'MDB mismatch' }
        } else {
            $dest = [IO.File]::Open($db,'CreateNew')
            try { $s.CopyTo($dest) } finally { $dest.Dispose() }
        }
    } finally { $s.Dispose() }
} finally { $archive.Dispose() }
$c = [Data.Odbc.OdbcConnection]::new('Driver={Microsoft Access Driver (*.mdb, *.accdb)};Readonly=1;DBQ='+ (Resolve-Path $db).Path)
try {
    $c.Open()
    $cmd = $c.CreateCommand()
    $cmd.CommandText = 'SELECT COUN,CITY,SUBJ,EMOT,SIT,PLEA,EXPC,INTS,CAUS FROM DATA'
    $t = [Data.DataTable]::new()
    $t.Load($cmd.ExecuteReader())
    $t | Select-Object COUN,CITY,SUBJ,EMOT,SIT,PLEA,EXPC,INTS,CAUS | Export-Csv (Join-Path $out 'isear.csv') -NoTypeInformation -NoClobber
} finally { $c.Dispose() }
