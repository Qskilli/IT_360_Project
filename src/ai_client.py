
#Built-in tool for JSON, a text format for structured data.	
#Turns the AI’s reply text into Python data the code can read, using json.loads(...) in _parse_response.
import json

#Built-in tool for reading settings from the computer.
#Reads the API key, server address and model name from environment variables with os.getenv(...), so the key never has to be written in the code.
import os

#Built-in “regular expressions” tool for finding patterns in text.	
#AI models often add extra words or code fences around their JSON. re.search(r"\{.*\}", ...) finds just the part between the first { and the last }.
import re

#A separate library (not built in) for sending web requests.	
#Sends the case description and law list to the AI server with requests.post(...) and gets the answer back. It also provides the error types (Timeout, ConnectionError) that the code catches.
import requests

# Settings come from environment variables so the API key never sits in the code.
# Address of the AI server; uses OLLAMA_BASE_URL if set, otherwise the ISU class server
BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://sushi.it.ilstu.edu:8080")
# Name of the AI model to use; uses OLLAMA_MODEL if set, otherwise "llama3"
MODEL = os.getenv("OLLAMA_MODEL", "llama3")
# Maximum number of seconds to wait for the AI to respond before giving up
TIMEOUT_SECONDS = 120

SYSTEM_PROMPT = (
    "You are a legal research assistant for Illinois digital forensic investigators. "
    "You only choose laws from the numbered list you are given. "
    "You always reply with valid JSON and nothing else."
)



class AIError(Exception):
    """Raised for any AI problem; the message is safe to show to the user."""


def _build_prompt(case_description: str, laws: list[dict]) -> str:
    """Combine the case description and the numbered law list into one prompt."""
    law_list = "\n".join(
        f"[{law['id']}] {law['citation']} - {law['title']}: {law['summary']}"
        for law in laws
    )
    return f"""Case description from the investigator:
\"\"\"{case_description}\"\"\"

Available Illinois laws:
{law_list}

Reply with JSON in exactly this format:
{{
  "facts": {{"crime_type": "...", "technology": "...", "evidence_type": "..."}},
  "laws": [{{"id": <law number>, "reason": "one sentence on why it applies"}}],
  "evidence_considerations": ["short tip", "short tip"]
}}
Only include laws that clearly apply. If none apply, return an empty "laws" list."""


def _parse_response(content: str, laws: list[dict]) -> dict:
    """Pull the JSON out of the AI's reply and keep only laws that really exist."""
    # Models sometimes wrap JSON in extra text or ``` fences, so grab the outermost {...}.
    match = re.search(r"\{.*\}", content, re.DOTALL)
    if not match:
        raise AIError("The AI reply was not in the expected format. Please try again.")
    try:
        data = json.loads(match.group())
    except json.JSONDecodeError:
        raise AIError("The AI reply could not be read. Please try again.")

    laws_by_id = {law["id"]: law for law in laws}
    matched_laws = []
    for item in data.get("laws", []):
        try:
            law_id = int(item.get("id"))
        except (TypeError, ValueError, AttributeError):
            continue  # skip entries without a usable ID
        if law_id in laws_by_id:  # ignore any ID the AI invented
            matched_laws.append({**laws_by_id[law_id], "reason": item.get("reason", "")})

    return {
        "facts": data.get("facts", {}),
        "laws": matched_laws,
        "evidence_considerations": data.get("evidence_considerations", []),
    }


def analyze_case(case_description: str, laws: list[dict]) -> dict:
    """Ask the AI which of the given laws apply to the case description."""
    api_key = os.getenv("OLLAMA_API_KEY")
    if not api_key:
        raise AIError("OLLAMA_API_KEY is not set. See the README for setup steps.")

    # The class server uses an OpenAI-style chat endpoint in front of Ollama.
    try:
        response = requests.post(
            f"{BASE_URL}/api/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": MODEL,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": _build_prompt(case_description, laws)},
                ],
                "temperature": 0,  # same input -> same answer, which suits legal lookups
                "stream": False,
            },
            timeout=TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
    except requests.Timeout:
        raise AIError("The AI server took too long to respond. Please try again.")
    except requests.ConnectionError:
        raise AIError("Could not reach the AI server. Are you on the ISU network or VPN?")
    except requests.HTTPError:
        raise AIError(f"The AI server returned an error (HTTP {response.status_code}).")
    except (ValueError, KeyError, IndexError):
        raise AIError("The AI server sent back an unexpected response.")

    return _parse_response(content, laws)
