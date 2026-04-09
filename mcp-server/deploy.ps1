# Nasta AS Kunde PoC - Deploy SQL MCP Server to Azure Container Apps
# Prerequisites: az cli logged in, Docker installed

param(
    [string]$ResourceGroup = "rg-nasta-poc",
    [string]$Location = "norwayeast",
    [string]$AcrName = "acrnastapoc",
    [string]$ContainerAppEnv = "cae-nasta-poc",
    [string]$ContainerAppName = "ca-nasta-mcp",
    [string]$SqlConnectionString
)

if (-not $SqlConnectionString) {
    Write-Error "SqlConnectionString parameter is required"
    exit 1
}

Write-Host "=== Step 1: Create Azure Container Registry ==="
az acr create --resource-group $ResourceGroup --name $AcrName --sku Basic --location $Location
az acr login --name $AcrName

Write-Host "=== Step 2: Build and push Docker image ==="
$ImageTag = "$AcrName.azurecr.io/nasta-mcp-server:latest"
docker build -t $ImageTag .
docker push $ImageTag

Write-Host "=== Step 3: Create Container Apps Environment ==="
az containerapp env create `
    --name $ContainerAppEnv `
    --resource-group $ResourceGroup `
    --location $Location

Write-Host "=== Step 4: Deploy Container App ==="
az containerapp create `
    --name $ContainerAppName `
    --resource-group $ResourceGroup `
    --environment $ContainerAppEnv `
    --image $ImageTag `
    --target-port 5000 `
    --ingress external `
    --registry-server "$AcrName.azurecr.io" `
    --min-replicas 0 `
    --max-replicas 1 `
    --secrets "mssql-conn=$SqlConnectionString" `
    --env-vars "MSSQL_CONNECTION_STRING=secretref:mssql-conn"

Write-Host "=== Deployment Complete ==="
$fqdn = az containerapp show --name $ContainerAppName --resource-group $ResourceGroup --query "properties.configuration.ingress.fqdn" -o tsv
Write-Host "MCP Server endpoint: https://$fqdn/mcp"
Write-Host "REST API endpoint: https://$fqdn/api"
