# Azure free-tier demo deployment

This guide deploys the existing VeriClaim API as a **public demo** on Azure
Container Apps. It deliberately uses one replica maximum and scales to zero
when idle. It does not make the application production-ready for real customer
data.

## Before you deploy

1. Create an Azure account and sign in with `az login`.
2. In Azure Cost Management, create a small budget alert before creating any
   resource. Free grants and eligibility differ by account and can change.
3. Confirm that the deployed bundle contains only demo-safe accounts, claims,
   and evidence. Do not upload real policyholder data.
4. Install Azure CLI and ensure Docker is available if Azure CLI asks to build
   the container locally.

## Deploy the API

From the project directory, run:

```powershell
.\scripts\deploy-azure-free.ps1 `
  -ResourceGroup vericlaim-demo-rg `
  -Location centralindia `
  -AppName vericlaim-demo
```

Azure CLI prints a HTTPS application URL. Verify these endpoints after it
finishes:

```text
https://YOUR-APP-URL/api/health
https://YOUR-APP-URL/
```

## Cost guardrails

- Leave `min replicas` at `0`; do not change it to `1` for a demo.
- Keep `max replicas` at `1` until load testing proves a need for more.
- Use the CPU model only. Cloud GPU inference is unnecessary for this demo and
  can rapidly exhaust a free-tier budget.
- Keep testing evidence small and delete it after the demo.
- Review the Azure Cost Analysis page after the first deployment.

## Current limitations

The local SQLite file is excluded from the container image, so claims, users,
and claim-passport history are **not durable across a container replacement**.
That is acceptable only for a temporary demo. Before production, replace it
with PostgreSQL, move uploads to private Blob Storage, use managed identities
and Key Vault, enable HTTPS-only access, and add a production identity provider.

## Frontend deployment

The Python server currently serves the UI and API together, which keeps the
demo simple. After the API is proven online, the static `app/static` frontend
can be moved to Azure Static Web Apps Free. Update its API base URL to the
Container Apps HTTPS URL and retain the API as the only place that loads the
fraud model.
