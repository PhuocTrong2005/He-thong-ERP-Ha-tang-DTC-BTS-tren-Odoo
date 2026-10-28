$ErrorActionPreference = 'Stop'
$local = Join-Path $PSScriptRoot '.local'
New-Item -ItemType Directory -Force -Path $local | Out-Null
$secretsPath = Join-Path $local 'credentials.json'
if (-not (Test-Path -LiteralPath $secretsPath)) {
    $secrets = @{}
    foreach ($key in @('db', 'master', 'admin', 'ksgs', 'bgd', 'infra')) {
        $bytes = New-Object byte[] 24
        $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
        $rng.GetBytes($bytes)
        $rng.Dispose()
        $secrets[$key] = [Convert]::ToBase64String($bytes)
    }
    $secrets | ConvertTo-Json | Set-Content -LiteralPath $secretsPath -Encoding UTF8
}
$secrets = Get-Content -LiteralPath $secretsPath -Raw | ConvertFrom-Json
"DEMO_DB_PASSWORD=$($secrets.db)" | Set-Content -LiteralPath (Join-Path $local '.env') -Encoding ASCII
@"
[options]
admin_passwd = $($secrets.master)
db_host = db
db_port = 5432
db_user = odoo
db_password = $($secrets.db)
db_name = bts_contract_demo
dbfilter = ^bts_contract_demo$
list_db = False
addons_path = /usr/lib/python3/dist-packages/odoo/addons,/mnt/extra-addons
data_dir = /var/lib/odoo
http_port = 8069
proxy_mode = False
smtp_server = mailpit
smtp_port = 1025
smtp_ssl = False
email_from = odoo@demo.invalid
workers = 0
limit_time_cpu = 600
limit_time_real = 1200
"@ | Set-Content -LiteralPath (Join-Path $local 'odoo.conf') -Encoding ASCII
Write-Output 'Demo configuration prepared; secrets remain in demo/.local/.'
