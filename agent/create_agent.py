"""Create Nasta Kundeservice agent in Azure AI Foundry via SDK."""

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import (
    FunctionTool,
    MCPTool,
    PromptAgentDefinition,
)
from azure.identity import DefaultAzureCredential

ENDPOINT = "https://swedencentral.api.azureml.ms"
SUBSCRIPTION_ID = "59aae656-c78b-4bc5-bcfd-e31748e6f6e2"
RESOURCE_GROUP = "rg-nasta-poc"
PROJECT_NAME = "proj-nasta-poc"

MODEL = "gpt-5-3-chat"
AGENT_NAME = "nasta-kundeservice"

MCP_SERVER_URL = "https://ca-nasta-mcp.salmonsmoke-ae79c912.norwayeast.azurecontainerapps.io"

INSTRUCTIONS = """Du er en kundeservice-assistent for Nasta AS, en leverandoer av anleggsmaskiner og tungt utstyr i Norge.

Dine oppgaver:
1. Slaa opp kundeinformasjon basert paa kundenummer, navn, eller organisasjonsnummer
2. Vise maskinparken til en kunde (alle maskiner tilknyttet kunden)
3. Vise ordrehistorikk og aktive ordrer for en kunde
4. Slaa opp firmainfo paa proff.no og at.no ved hjelp av organisasjonsnummer

Retningslinjer:
- Svar alltid paa norsk
- Presenter data i oversiktlige tabeller naar det er hensiktsmessig
- Bruk MCP-verktoyene (Nasta Database) for aa hente kunde-, maskin- og ordredata
- Naar du slaar opp paa proff.no, bruk lookup_proff-funksjonen med org_nummer
- Naar du slaar opp paa at.no, bruk lookup_at-funksjonen med org_nummer
- Hvis kunden har mange maskiner/ordrer, oppsummer foerst og tilby aa vise detaljer
"""


def main():
    credential = DefaultAzureCredential()

    client = AIProjectClient(
        endpoint=ENDPOINT,
        subscription_id=SUBSCRIPTION_ID,
        resource_group_name=RESOURCE_GROUP,
        project_name=PROJECT_NAME,
        credential=credential,
    )

    # Build tools
    tools = []

    # 1. MCP Tool - Data API Builder for database access
    tools.append(MCPTool(
        server_label="Nasta Database",
        server_url=f"{MCP_SERVER_URL}/api",
        server_description="Nasta AS kunderegister. REST API med OData filter. Tabeller: Customers (kundenummer, navn, adresse, epost, telefonnummer, org_nummer), Machines (device_id, kundenummer, maskin_navn, aarsmodell, chassisnummer), Orders (ordrenummer, kundenummer, ordretype, beskrivelse, device_id, status, opprettet_dato, symptomer_feil).",
        require_approval="never",
    ))
    print(f"Added MCP Tool: {MCP_SERVER_URL}/api")

    # 2. Function tools for web lookups
    tools.append(FunctionTool(
        name="lookup_proff",
        description="Slaa opp firmainformasjon paa proff.no basert paa organisasjonsnummer. Returnerer firmanavn, adresse, bransje, okonomi.",
        parameters={
            "type": "object",
            "properties": {
                "org_nummer": {
                    "type": "string",
                    "description": "Norsk organisasjonsnummer (9 siffer)",
                }
            },
            "required": ["org_nummer"],
        },
    ))
    tools.append(FunctionTool(
        name="lookup_at",
        description="Slaa opp firmainformasjon paa at.no (Arbeidstilsynet) basert paa organisasjonsnummer. Returnerer tilsynsdata og HMS-info.",
        parameters={
            "type": "object",
            "properties": {
                "org_nummer": {
                    "type": "string",
                    "description": "Norsk organisasjonsnummer (9 siffer)",
                }
            },
            "required": ["org_nummer"],
        },
    ))
    print("Added function tools: lookup_proff, lookup_at")

    # Create agent definition
    definition = PromptAgentDefinition(
        model=MODEL,
        instructions=INSTRUCTIONS,
        tools=tools,
    )

    # Create agent version
    agent = client.agents.create_version(
        agent_name=AGENT_NAME,
        definition=definition,
        description="Nasta AS kundeservice-agent med tilgang til kundedata, maskinpark og ordrehistorikk.",
    )

    print(f"\nAgent created!")
    print(f"  Name:    {AGENT_NAME}")
    print(f"  Version: {agent.version}")
    print(f"  Model:   {MODEL}")
    print(f"  ID:      {agent.id}")
    return agent


if __name__ == "__main__":
    main()
