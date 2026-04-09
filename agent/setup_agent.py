"""
Nasta AS Kunde PoC - Create/update Foundry Agent via SDK.
Requires environment variables:
  - AZURE_AI_PROJECT_CONNECTION_STRING
  - MCP_SERVER_URL (Data API Builder MCP endpoint)
  - LOOKUP_FUNCTION_URL (Azure Functions base URL)
  - LOOKUP_FUNCTION_KEY (Azure Functions host key)
"""

import os

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import (
    BingGroundingTool,
    FunctionTool,
    OpenApiTool,
)
from azure.identity import DefaultAzureCredential

# --- Configuration ---
PROJECT_CONN = os.environ["AZURE_AI_PROJECT_CONNECTION_STRING"]
MCP_SERVER_URL = os.environ["MCP_SERVER_URL"]
LOOKUP_FUNCTION_URL = os.environ.get("LOOKUP_FUNCTION_URL", "")
LOOKUP_FUNCTION_KEY = os.environ.get("LOOKUP_FUNCTION_KEY", "")

AGENT_NAME = "Nasta Kundeservice"
MODEL = "gpt-5.3-chat"

INSTRUCTIONS = """Du er en kundeservice-assistent for Nasta AS, en leverandoer av anleggsmaskiner og tungt utstyr i Norge.

Dine oppgaver:
1. Slaa opp kundeinformasjon basert paa kundenummer, navn, eller organisasjonsnummer
2. Vise maskinparken til en kunde (alle maskiner tilknyttet kunden)
3. Vise ordrehistorikk og aktive ordrer for en kunde
4. Slaa opp firmainfo paa proff.no og at.no ved hjelp av organisasjonsnummer

Retningslinjer:
- Svar alltid paa norsk
- Presenter data i oversiktlige tabeller naar det er hensiktsmessig
- Naar du slaar opp paa proff.no, bruk lookup_proff-funksjonen med org_nummer. Hvis den feiler, soek via Bing med "site:proff.no {org_nummer}"
- Naar du slaar opp paa at.no, bruk lookup_at-funksjonen med org_nummer. Hvis den feiler, soek via Bing med "site:at.no {firmanavn}"
- Hvis kunden har mange maskiner/ordrer, oppsummer foerst og tilby aa vise detaljer
- Bruk MCP-verktoyene for aa soeke i kundedatabasen
- Ved feil i oppslag, proev igjen foer du gir opp

Eksempel paa svar:
"Kunde 1001 - Berge AS:
| Felt | Verdi |
|------|-------|
| Navn | Berge AS |
| Adresse | Storgata 1, 0100 Oslo |
| Org.nr | 912345678 |
| Maskiner | 5 stk |
| Aktive ordrer | 3 stk |"
"""

# Lookup function definitions for the agent
LOOKUP_FUNCTIONS = [
    {
        "type": "function",
        "function": {
            "name": "lookup_proff",
            "description": "Slaa opp firmainformasjon paa proff.no basert paa organisasjonsnummer. Returnerer firmainfo, okonomi og kontaktdata.",
            "parameters": {
                "type": "object",
                "properties": {
                    "org_nummer": {
                        "type": "string",
                        "description": "Norsk organisasjonsnummer (9 siffer)",
                    }
                },
                "required": ["org_nummer"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "lookup_at",
            "description": "Slaa opp firmainformasjon paa at.no basert paa organisasjonsnummer. Returnerer tilsynsdata og HMS-info.",
            "parameters": {
                "type": "object",
                "properties": {
                    "org_nummer": {
                        "type": "string",
                        "description": "Norsk organisasjonsnummer (9 siffer)",
                    }
                },
                "required": ["org_nummer"],
            },
        },
    },
]


def main():
    credential = DefaultAzureCredential()
    client = AIProjectClient.from_connection_string(
        conn_str=PROJECT_CONN, credential=credential
    )

    # Build tool list
    tools = []

    # 1. Bing Grounding for web search fallback
    bing_connection = client.connections.get_default(
        connection_type="BingGrounding"
    )
    if bing_connection:
        tools.append(BingGroundingTool(connection_id=bing_connection.id))
        print(f"Added Bing Grounding tool (connection: {bing_connection.id})")

    # 2. Function tools for proff.no/at.no lookup
    tools.append(FunctionTool(functions=LOOKUP_FUNCTIONS))
    print("Added lookup function tools (lookup_proff, lookup_at)")

    # Create the agent
    agent = client.agents.create_agent(
        model=MODEL,
        name=AGENT_NAME,
        instructions=INSTRUCTIONS,
        tools=tools,
    )

    print(f"\nAgent created successfully!")
    print(f"  Agent ID: {agent.id}")
    print(f"  Name: {agent.name}")
    print(f"  Model: {agent.model}")
    print(f"\nNote: Add the MCP Server tool manually in the Foundry portal:")
    print(f"  URL: {MCP_SERVER_URL}")
    print(f"  This connects the agent to the Nasta customer database.")


if __name__ == "__main__":
    main()
