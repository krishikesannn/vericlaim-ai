<#
Deploy the demo API to Azure Container Apps using the consumption plan.

This script deliberately uses one replica at most and scales to zero when idle.
Run only after `az login`; it creates Azure resources and may incur charges if
the account exceeds Azure's free allowance. Set a subscription budget first.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$ResourceGroup,

    [Parameter(Mandatory = $true)]
    [string]$Location,

    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[a-z0-9-]{2,32}$')]
    [string]$AppName
)

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot

if (-not (Get-Command az -ErrorAction SilentlyContinue)) {
    throw 'Azure CLI is required. Install it, then run az login before deploying.'
}

az account show --output none
if ($LASTEXITCODE -ne 0) {
    throw 'No active Azure login. Run az login, select the intended subscription, then retry.'
}

az group create --name $ResourceGroup --location $Location --output none
if ($LASTEXITCODE -ne 0) { throw 'Could not create or access the resource group.' }

Push-Location $projectRoot
try {
    az containerapp up `
        --name $AppName `
        --resource-group $ResourceGroup `
        --location $Location `
        --source . `
        --ingress external `
        --target-port 8080 `
        --env-vars VERICLAIM_HOST=0.0.0.0 VERICLAIM_PORT=8080

    if ($LASTEXITCODE -ne 0) { throw 'Azure Container Apps deployment failed.' }

    # Azure CLI versions differ: scale flags belong to `containerapp update`,
    # not `containerapp up`, in the CLI available for this project.
    az containerapp update `
        --name $AppName `
        --resource-group $ResourceGroup `
        --min-replicas 0 `
        --max-replicas 1 `
        --output none

    if ($LASTEXITCODE -ne 0) { throw 'Could not apply the demo scale guardrails.' }
} finally {
    Pop-Location
}

Write-Host 'Deployment completed. Record the generated HTTPS URL and immediately configure a budget alert.'
