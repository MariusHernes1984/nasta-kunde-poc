# Nasta AS Kundeservice PoC

AI-drevet kundeservice-agent for Nasta AS. Slaar opp kundeinformasjon, maskinpark og ordrehistorikk, med integrasjon mot proff.no og at.no.

## Arkitektur

```
Azure SQL Database  -->  Data API Builder (MCP Server)  -->  Azure AI Foundry Agent (GPT 5.3-chat)
  3 tabeller              Container Apps                      + Bing Grounding + Azure Functions
  50 mock-kunder           Read-only                                    |
                                                              React Webapp (Static Web Apps)
```

## Oppsett

### 1. Generer mock-data

```bash
cd data
pip install -r requirements.txt
python generate_mock_data.py
# Genererer seed_data.sql med 50 kunder, ~186 maskiner, ~389 ordrer
```

### 2. Opprett Azure SQL Database

```bash
az group create --name rg-nasta-poc --location norwayeast
az sql server create --name sql-nasta-poc --resource-group rg-nasta-poc --location norwayeast --admin-user sqladmin --admin-password <password>
az sql server firewall-rule create --server sql-nasta-poc --resource-group rg-nasta-poc --name AllowAzure --start-ip-address 0.0.0.0 --end-ip-address 0.0.0.0
az sql db create --server sql-nasta-poc --resource-group rg-nasta-poc --name NastaDB --service-objective S0
```

Kjoer SQL-filene:
```bash
sqlcmd -S sql-nasta-poc.database.windows.net -d NastaDB -U sqladmin -P <password> -i data/schema.sql
sqlcmd -S sql-nasta-poc.database.windows.net -d NastaDB -U sqladmin -P <password> -i data/seed_data.sql
```

### 3. Deploy MCP Server (Data API Builder)

```bash
cd mcp-server
# Sett MSSQL_CONNECTION_STRING og kjoer deploy-scriptet:
./deploy.ps1 -SqlConnectionString "Server=sql-nasta-poc.database.windows.net;Database=NastaDB;User Id=sqladmin;Password=<password>;Encrypt=true"
```

### 4. Deploy Azure Functions (proff.no/at.no lookup)

```bash
cd functions
func azure functionapp publish <function-app-name>
```

### 5. Opprett Foundry Agent

**Via portalen (anbefalt):**
1. Gaa til ai.azure.com, velg prosjektet
2. Opprett ny agent med modell `gpt-5.3-chat`
3. Legg til verktoy:
   - Custom MCP Tool → MCP Server URL fra steg 3
   - Bing Grounding → koble til Bing-tilkobling
   - Function tools → Azure Functions fra steg 4
4. Lim inn system-prompt fra `agent/setup_agent.py`

**Via SDK:**
```bash
cd agent
pip install -r requirements.txt
export AZURE_AI_PROJECT_CONNECTION_STRING="<connection-string>"
export MCP_SERVER_URL="https://<app>.azurecontainerapps.io/mcp"
python setup_agent.py
```

### 6. Start webapp

```bash
cd webapp
npm install
npm run dev
```

Sett `VITE_AGENT_API_URL` i `.env` for aa peke til agent-API-et.

## Datadistribusjon

| Aktivitetsnivaa | Antall kunder | Maskiner per kunde | Ordrer per kunde |
|-----------------|---------------|--------------------|------------------|
| Lav             | ~15           | 1                  | 0-1              |
| Middels         | ~20           | 2-4                | 3-8              |
| Hoey            | ~15           | 5-10               | 10-25            |
