"""
Nasta AS - Backend proxy: AI chat + database access + web lookups.
Azure Function that orchestrates GPT 5.3-chat with function calling.
"""

import asyncio
import json
import logging
import os
import re
import uuid

import azure.functions as func
import httpx

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

# --- Config ---
AOAI_ENDPOINT = os.environ.get("AOAI_ENDPOINT", "https://aoai-nasta-poc.openai.azure.com")
AOAI_KEY = os.environ.get("AOAI_KEY", "")
AOAI_DEPLOYMENT = os.environ.get("AOAI_DEPLOYMENT", "gpt-5-3-chat")
AOAI_API_VERSION = "2025-04-01-preview"
MCP_SERVER_URL = os.environ.get("MCP_SERVER_URL", "https://ca-nasta-mcp.salmonsmoke-ae79c912.norwayeast.azurecontainerapps.io")

MAX_RETRIES = 3
BASE_DELAY = 1.0

SYSTEM_PROMPT = """Du er en kundeservice-assistent for Nasta AS, en leverandoer av anleggsmaskiner og tungt utstyr i Norge.

Dine oppgaver:
1. Slaa opp kundeinformasjon basert paa kundenummer, navn, eller organisasjonsnummer
2. Vise maskinparken til en kunde (alle maskiner tilknyttet kunden)
3. Vise ordrehistorikk og aktive ordrer for en kunde
4. Slaa opp firmainfo paa proff.no og at.no ved hjelp av organisasjonsnummer

Retningslinjer:
- Svar alltid paa norsk
- Presenter data i oversiktlige tabeller naar det er hensiktsmessig
- Hvis kunden har mange maskiner/ordrer, oppsummer foerst og tilby aa vise detaljer
- Vær presis og hjelpsom
"""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "query_customers",
            "description": "Hent kundeinformasjon fra Nasta-databasen. Soek paa kundenummer eller org_nummer. Uten parametere returneres alle kunder.",
            "parameters": {
                "type": "object",
                "properties": {
                    "kundenummer": {
                        "type": "integer",
                        "description": "Kundenummer (f.eks. 1001)",
                    },
                    "org_nummer": {
                        "type": "string",
                        "description": "Organisasjonsnummer (f.eks. 860806024)",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "query_machines",
            "description": "Hent maskiner fra Nasta-databasen. Soek paa kundenummer for aa faa alle maskiner til en kunde.",
            "parameters": {
                "type": "object",
                "properties": {
                    "kundenummer": {
                        "type": "integer",
                        "description": "Kundenummer for aa hente maskinpark",
                    },
                    "device_id": {
                        "type": "string",
                        "description": "Unik maskin-ID (f.eks. NAS-1001-001)",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "query_orders",
            "description": "Hent ordrer fra Nasta-databasen. Soek paa kundenummer for aa faa alle ordrer til en kunde.",
            "parameters": {
                "type": "object",
                "properties": {
                    "kundenummer": {
                        "type": "integer",
                        "description": "Kundenummer for aa hente ordrer",
                    },
                    "device_id": {
                        "type": "string",
                        "description": "Maskin device_id for aa hente ordrer for en spesifikk maskin",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "lookup_proff",
            "description": "Slaa opp firmainformasjon paa proff.no basert paa organisasjonsnummer. Returnerer firmanavn, adresse, bransje, oekonomisk info.",
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
            "description": "Slaa opp firmainformasjon paa at.no (Arbeidstilsynet) basert paa organisasjonsnummer. Returnerer tilsynsdata og HMS-info.",
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

# In-memory thread storage (for PoC)
threads: dict[str, list[dict]] = {}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
    "Accept-Language": "nb-NO,nb;q=0.9,no;q=0.8,en;q=0.5",
}


async def fetch_with_retry(url: str, params: dict | None = None) -> str | None:
    """Fetch URL with up to 3 retries and exponential backoff."""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            async with httpx.AsyncClient(
                timeout=15.0, follow_redirects=True, headers=HEADERS
            ) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                return response.text
        except (httpx.HTTPStatusError, httpx.RequestError, httpx.TimeoutException) as e:
            logging.warning(f"Attempt {attempt}/{MAX_RETRIES} failed for {url}: {e}")
            if attempt < MAX_RETRIES:
                delay = BASE_DELAY * (2 ** (attempt - 1))
                await asyncio.sleep(delay)
    return None


def extract_text(html: str) -> str:
    """Basic HTML text extraction."""
    text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL)
    text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:3000]


async def query_dab(entity: str, filter_field: str | None = None, filter_value: str | int | None = None) -> str:
    """Query Data API Builder. For PK lookups uses /entity/pk/val, otherwise fetches all and filters."""
    async with httpx.AsyncClient(timeout=15.0) as client:
        # Primary key lookups work via URL path
        pk_fields = {"Customers": "kundenummer", "Machines": "device_id", "Orders": "ordrenummer"}
        pk = pk_fields.get(entity)

        if filter_field and filter_field == pk and filter_value is not None:
            url = f"{MCP_SERVER_URL}/api/{entity}/{pk}/{filter_value}"
            resp = await client.get(url)
            return resp.text

        # For non-PK filters, fetch all and filter in memory (fine for PoC with <500 rows)
        url = f"{MCP_SERVER_URL}/api/{entity}"
        resp = await client.get(url)
        if not filter_field or filter_value is None:
            return resp.text

        data = resp.json()
        filtered = [
            r for r in data.get("value", [])
            if str(r.get(filter_field, "")) == str(filter_value)
        ]
        return json.dumps({"value": filtered})


async def execute_function(name: str, args: dict) -> str:
    """Execute a function tool call and return the result as JSON string."""
    try:
        if name == "query_customers":
            if args.get("kundenummer"):
                return await query_dab("Customers", "kundenummer", args["kundenummer"])
            elif args.get("org_nummer"):
                return await query_dab("Customers", "org_nummer", args["org_nummer"])
            return await query_dab("Customers")

        elif name == "query_machines":
            if args.get("device_id"):
                return await query_dab("Machines", "device_id", args["device_id"])
            elif args.get("kundenummer"):
                return await query_dab("Machines", "kundenummer", args["kundenummer"])
            return await query_dab("Machines")

        elif name == "query_orders":
            if args.get("kundenummer"):
                return await query_dab("Orders", "kundenummer", args["kundenummer"])
            elif args.get("device_id"):
                return await query_dab("Orders", "device_id", args["device_id"])
            return await query_dab("Orders")

        elif name == "lookup_proff":
            org = args.get("org_nummer", "").replace(" ", "")
            html = await fetch_with_retry("https://www.proff.no/bransjesok", {"q": org})
            if html:
                return json.dumps({"source": "proff.no", "org_nummer": org, "content": extract_text(html)})
            return json.dumps({"error": "Could not reach proff.no after 3 attempts", "org_nummer": org})

        elif name == "lookup_at":
            org = args.get("org_nummer", "").replace(" ", "")
            html = await fetch_with_retry("https://www.at.no/search", {"q": org})
            if html:
                return json.dumps({"source": "at.no", "org_nummer": org, "content": extract_text(html)})
            return json.dumps({"error": "Could not reach at.no after 3 attempts", "org_nummer": org})

        return json.dumps({"error": f"Unknown function: {name}"})
    except Exception as e:
        return json.dumps({"error": str(e)})


async def chat_completion(messages: list[dict]) -> dict:
    """Call Azure OpenAI with function calling, handling tool calls in a loop."""
    url = f"{AOAI_ENDPOINT}/openai/deployments/{AOAI_DEPLOYMENT}/chat/completions?api-version={AOAI_API_VERSION}"
    headers = {"Content-Type": "application/json", "api-key": AOAI_KEY}

    current_messages = list(messages)
    max_rounds = 5

    for _ in range(max_rounds):
        body = {
            "messages": current_messages,
            "tools": TOOLS,
            "tool_choice": "auto",
            "max_completion_tokens": 2000,
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(url, json=body, headers=headers)
            resp.raise_for_status()
            data = resp.json()

        choice = data["choices"][0]
        assistant_msg = choice["message"]
        current_messages.append(assistant_msg)

        if choice.get("finish_reason") == "tool_calls" or assistant_msg.get("tool_calls"):
            tool_calls = assistant_msg.get("tool_calls", [])
            for tc in tool_calls:
                fn_name = tc["function"]["name"]
                fn_args = json.loads(tc["function"]["arguments"])
                logging.info(f"Calling function: {fn_name}({fn_args})")
                result = await execute_function(fn_name, fn_args)
                current_messages.append({
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "content": result,
                })
        else:
            return {"content": assistant_msg.get("content", ""), "messages": current_messages}

    return {"content": "Beklager, for mange funksjonskall. Proev igjen.", "messages": current_messages}


@app.route(route="chat", methods=["POST", "OPTIONS"])
async def chat(req: func.HttpRequest) -> func.HttpResponse:
    """Main chat endpoint. Accepts {message, threadId?} and returns AI response."""
    # CORS
    if req.method == "OPTIONS":
        return func.HttpResponse(
            "",
            status_code=200,
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type",
            },
        )

    try:
        body = req.get_json()
    except ValueError:
        return func.HttpResponse(
            json.dumps({"error": "Invalid JSON"}),
            status_code=400,
            mimetype="application/json",
        )

    message = body.get("message", "").strip()
    thread_id = body.get("threadId")

    if not message:
        return func.HttpResponse(
            json.dumps({"error": "message is required"}),
            status_code=400,
            mimetype="application/json",
        )

    # Get or create thread
    if not thread_id or thread_id not in threads:
        thread_id = str(uuid.uuid4())
        threads[thread_id] = [{"role": "system", "content": SYSTEM_PROMPT}]

    # Add user message
    threads[thread_id].append({"role": "user", "content": message})

    # Get AI response
    result = await chat_completion(threads[thread_id])
    threads[thread_id] = result["messages"]

    response_body = json.dumps({
        "message": result["content"],
        "threadId": thread_id,
    })

    return func.HttpResponse(
        response_body,
        mimetype="application/json",
        headers={"Access-Control-Allow-Origin": "*"},
    )


SUMMARY_SYSTEM_PROMPT = """Du er en salgsanalytiker for Nasta AS, en leverandoer av anleggsmaskiner i Norge.

Du mottar kundedata, maskinpark og ordrehistorikk i JSON-format.
Analyser dataene og returner ALLTID et gyldig JSON-objekt med NOYAKTIG denne strukturen:

{
  "summary": "2-4 setninger som oppsummerer kunden: aktivitetsnivaa, maskinpark-tilstand, ordretrender og viktige observasjoner.",
  "upsells": [
    {
      "title": "Kort tittel (maks 8 ord)",
      "description": "1-2 setninger med konkret begrunnelse basert paa dataene.",
      "priority": "high|medium|low"
    }
  ]
}

Regler for analyse:
- Maskiner med aarsmodell eldre enn 2018 er kandidater for oppgradering
- Mange reparasjonsordrer paa samme maskin = foreslaa servicekontrakt
- Kunder med kun gravemaskiner men ingen hjullastere = kryssalg-mulighet
- Ingen ordrer siste 6 mnd (basert paa opprettet_dato) = churn-risiko
- Hoeyt antall ordrer med status "Mottatt" eller "Under behandling" = aktiv kunde
- Ordretype "Garanti" = maskinproblemer, vurder oppfoelging
- Gi 2-4 upsell-anbefalinger, sortert etter prioritet (high foerst)
- Skriv ALT paa norsk
- Returner KUN JSON, ingen annen tekst"""


@app.route(route="customer-summary", methods=["POST", "OPTIONS"])
async def customer_summary(req: func.HttpRequest) -> func.HttpResponse:
    """AI-powered customer summary + upsell recommendations."""
    if req.method == "OPTIONS":
        return func.HttpResponse(
            "", status_code=200,
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type",
            },
        )

    try:
        body = req.get_json()
    except ValueError:
        return func.HttpResponse(
            json.dumps({"error": "Invalid JSON"}), status_code=400, mimetype="application/json",
        )

    kundenummer = body.get("kundenummer")
    if not kundenummer:
        return func.HttpResponse(
            json.dumps({"error": "kundenummer is required"}), status_code=400, mimetype="application/json",
        )

    try:
        # Fetch all data from DAB in parallel
        customer_data, machines_data, orders_data = await asyncio.gather(
            query_dab("Customers", "kundenummer", kundenummer),
            query_dab("Machines", "kundenummer", kundenummer),
            query_dab("Orders", "kundenummer", kundenummer),
        )

        user_prompt = f"""Analyser denne kunden og gi oppsummering + salgsanbefalinger.

KUNDEDATA:
{customer_data}

MASKINPARK:
{machines_data}

ORDREHISTORIKK:
{orders_data}"""

        url = f"{AOAI_ENDPOINT}/openai/deployments/{AOAI_DEPLOYMENT}/chat/completions?api-version={AOAI_API_VERSION}"
        headers = {"Content-Type": "application/json", "api-key": AOAI_KEY}
        api_body = {
            "messages": [
                {"role": "system", "content": SUMMARY_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            "max_completion_tokens": 1500,
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(url, json=api_body, headers=headers)
            resp.raise_for_status()
            data = resp.json()

        content = data["choices"][0]["message"]["content"]

        # Strip markdown code fences if present
        content = content.strip()
        if content.startswith("```"):
            content = re.sub(r"^```(?:json)?\s*", "", content)
            content = re.sub(r"\s*```$", "", content)

        result = json.loads(content)

        return func.HttpResponse(
            json.dumps(result, ensure_ascii=False),
            mimetype="application/json",
            headers={"Access-Control-Allow-Origin": "*"},
        )
    except json.JSONDecodeError:
        logging.error(f"GPT returned invalid JSON: {content}")
        return func.HttpResponse(
            json.dumps({"summary": content, "upsells": []}),
            mimetype="application/json",
            headers={"Access-Control-Allow-Origin": "*"},
        )
    except Exception as e:
        logging.error(f"Summary error: {e}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}), status_code=500, mimetype="application/json",
            headers={"Access-Control-Allow-Origin": "*"},
        )


@app.route(route="health", methods=["GET"])
async def health(req: func.HttpRequest) -> func.HttpResponse:
    """Health check endpoint."""
    return func.HttpResponse(
        json.dumps({"status": "ok", "model": AOAI_DEPLOYMENT}),
        mimetype="application/json",
    )
