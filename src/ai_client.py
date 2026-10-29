
#This is a built-in tool for JSON, a text format for structured data.	
#It turns the AI’s reply text into Python data that the code can read.
import json

#This is a built-in tool for reading settings from the operating system.
#It reads the API key, server address and model name from environment variables, so the key never has to be written in the code.
import os

#This is uilt-in “regular expressions” tool for finding patterns in text.	
#AI models often add extra words or code fences around their JSON. re.search(r"\{.*\}", ...) finds just the part between the first { and the last }.
import re

#This is a separate library that is not built in built in by default for sending web requests.	
#It sends the case description and law list to the AI server with requests.post(...) and gets the answer back. 
import requests

# These Settings come from environment variables so the API key is secure and never sits in the code.
# This is the address of the AI server. It uses OLLAMA_BASE_URL if set, otherwise the ISU class server
BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://sushi.it.ilstu.edu:8080")
# This is the name of the AI model to use, It uses OLLAMA_MODEL if set, otherwise "llama3"
MODEL = os.getenv("OLLAMA_MODEL", "llama3")
# This is the maximum number of seconds to wait for the AI to respond before giving up
TIMEOUT_SECONDS = 120

# These are standing instructions sent to the AI with every request, telling it its role and rules
SYSTEM_PROMPT = (
    "You are a legal research assistant for Illinois digital forensic investigators. "
# Stops the AI from suggesting laws that aren't in our established database
    "You only choose laws from the numbered list you are given. "
# Asks for JSON only, so the program can read the answer reliably
    "You always reply with valid JSON and nothing else."
)


# This is a recommended custom error type for AI problems, so the frontend can catch it and show the message
class AIError(Exception):
    """Raised for any AI problem; the message is safe to show to the user."""

# This builds the full question sent to the AI from the case description from the frontend and the law list in the database
def _build_prompt(case_description: str, laws: list[dict]) -> str:
    """Combine the case description and the numbered law list into one prompt."""
    # This turns each law into one line like "[1] 720 ILCS 5/17-51 - Title: summary", one per line
    law_list = "\n".join(
        f"[{law['id']}] {law['title']} ({law['citation']}, {law['jurisdiction']}): "
        f"{law['summary']} Topics: {law['tags']}"
        for law in laws
    )
    # This returns the prompt: the case, the numbered laws, and the exact JSON format to reply in.
    # (Doubled {{ }} print as single braces; single { } insert a variable's value.)
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

# This turns the AI's text reply into a structured result the frontend can display
def _parse_response(content: str, laws: list[dict]) -> dict:
    """Pull the JSON out of the AI's reply and keep only laws that really exist."""
    # Since models sometimes wrap JSON in extra text or ``` fences, so grab the outermost {...}.
    match = re.search(r"\{.*\}", content, re.DOTALL)
    # If no {...} was found, then the reply is unusable, so it will report an error
    if not match:
        raise AIError("The AI reply was not in the expected format. Please try again.")
    # This converts the JSON text into a Python dictionary
    try:
        data = json.loads(match.group())
    # This handles the case where the text looked like JSON but wasn't valid
    except json.JSONDecodeError:
        raise AIError("The AI reply could not be read. Please try again.")
    
    # This builds a lookup table from law ID to the full law
    laws_by_id = {law["id"]: law for law in laws}
    # The empty list that will hold the laws the AI picked that really exist
    matched_laws = []
    # This goes through each law the AI picked (or nothing, if the "laws" key is missing)
    for item in data.get("laws", []):
        # This converts the ID to a whole number, since the AI may send "3" instead of 3
        try:
            law_id = int(item.get("id"))
        except (TypeError, ValueError, AttributeError):
            continue  # skip entries without a usable ID
        if law_id in laws_by_id:  # ignore any ID the AI invented
            # This adds the full law from the database plus the AI's reason it applies
            matched_laws.append({**laws_by_id[law_id], "reason": item.get("reason", "")})
    
    # This returns the results, using empty defaults for anything the AI left out
    return {
        # Facts the AI pulled from the case (crime type, technology, evidence type)
        "facts": data.get("facts", {}),
        # Only the verified laws from the database
        "laws": matched_laws,
        # The AI's evidence-handling tips
        "evidence_considerations": data.get("evidence_considerations", []),
    }

# This is the main function the front end calls: sends the case to the AI and returns the results
def analyze_case(case_description: str, laws: list[dict]) -> dict:
    """Ask the AI which of the given laws apply to the case description."""
    # This reads the API key from the computer's environment variables
    api_key = os.getenv("OLLAMA_API_KEY")
    # This stops early with a clear message if no API key has been set
    if not api_key:
        raise AIError("OLLAMA_API_KEY is not set. See the README for setup steps.")

    # The class server uses an OpenAI-style chat endpoint in front of Ollama.
    try:
        # This sends the request to the AI server and waits for the reply
        response = requests.post(
            # Full web address of the server's chat endpoint
            f"{BASE_URL}/api/chat/completions",
            # This sends the API key so the server knows we're allowed to use it
            headers={"Authorization": f"Bearer {api_key}"},
            # The request body, sent as JSON
            json={
                # Which AI model to use
                "model": MODEL,
                # The conversation: the standing rules first, then the actual question
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": _build_prompt(case_description, laws)},
                ],
                "temperature": 0,  # same input -> same answer, which suits legal lookups
                # This gets the whole reply at once instead of word by word
                "stream": False,
            },
            # This allows it to give up if the server takes longer than TIMEOUT_SECONDS
            timeout=TIMEOUT_SECONDS,
        )
        # This turns an HTTP error status (like 401 or 500) into an exception
        response.raise_for_status()
        # This digs the AI's text answer out of the server's JSON response
        content = response.json()["choices"][0]["message"]["content"]
    # The server didn't answer in time
    except requests.Timeout:
        raise AIError("The AI server took too long to respond. Please try again.")
        # The server couldn't be reached at all (wrong address, or off the ISU network)
    except requests.ConnectionError:
        raise AIError("Could not reach the AI server. Are you on the ISU network or VPN?")
        # The server answered with an error status, such as a bad API key
    except requests.HTTPError:
        raise AIError(f"The AI server returned an error (HTTP {response.status_code}).")
        # The server's response wasn't shaped the way it was expected
    except (ValueError, KeyError, IndexError):
        raise AIError("The AI server sent back an unexpected response.")
    
    # This checks the AI's answer and returns the verified results
    return _parse_response(content, laws)
