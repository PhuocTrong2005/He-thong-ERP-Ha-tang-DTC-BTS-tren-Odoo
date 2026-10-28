param(
    [ValidateSet('Start','Stop','Restart','Logs','Status','Seed','Verify','Finalize','BindViews','Inspect','Exceptions','Accounts')]
    [string]$Action = 'Status'
)
$ErrorActionPreference = 'Stop'
$composeArgs = @('compose', '--env-file', (Join-Path $PSScriptRoot '.local/.env'), '-f', (Join-Path $PSScriptRoot 'compose.yml'))
switch ($Action) {
    'Start' { & docker @composeArgs up -d }
    'Stop' { & docker @composeArgs stop }
    'Restart' { & docker @composeArgs restart }
    'Logs' { & docker @composeArgs logs --tail 100 -f odoo proxy }
    'Status' { & docker @composeArgs ps }
    'Seed' { & docker @composeArgs exec -T odoo sh -c 'odoo shell -c /etc/odoo/odoo.conf -d bts_contract_demo --no-http --log-level=warn < /mnt/demo/seed.py' }
    'Verify' { & docker @composeArgs exec -T odoo python3 /mnt/demo/verify.py }
    'Finalize' { & docker @composeArgs exec -T odoo sh -c 'odoo shell -c /etc/odoo/odoo.conf -d bts_contract_demo --no-http --log-level=warn < /mnt/demo/finalize.py' }
    'BindViews' { & docker @composeArgs exec -T odoo sh -c 'odoo shell -c /etc/odoo/odoo.conf -d bts_contract_demo --no-http --log-level=warn < /mnt/demo/bind_project_views.py' }
    'Inspect' { & docker @composeArgs exec -T odoo sh -c 'odoo shell -c /etc/odoo/odoo.conf -d bts_contract_demo --no-http --log-level=error < /mnt/demo/inspect_demo.py' }
    'Exceptions' { & docker @composeArgs exec -T odoo sh -c 'odoo shell -c /etc/odoo/odoo.conf -d bts_contract_demo --no-http --log-level=warn < /mnt/demo/seed_exceptions.py' }
    'Accounts' {
        $secrets = Get-Content -LiteralPath (Join-Path $PSScriptRoot '.local/credentials.json') -Raw | ConvertFrom-Json
        foreach ($role in @('ksgs','bgd','infra','admin')) {
            [PSCustomObject]@{ Login = "$role.demo"; Password = $secrets.$role }
        }
    }
}
if ($Action -ne 'Accounts' -and $LASTEXITCODE -ne 0) { throw "Docker failed with exit code $LASTEXITCODE" }
