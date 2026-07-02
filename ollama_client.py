import asyncio
import httpx
import json
import re
import json_repair

class OllamaClient:
    def __init__(self, host="http://localhost:11434", model="tinyllama:latest", max_concurrency=2):
        self.host = host
        self.model = model
        self.timeout = 120.0
        self.semaphore = asyncio.Semaphore(max_concurrency)

    async def generate(self, prompt: str, system_prompt: str = "", temperature: float = 0.7) -> str:
        """Call Ollama's /api/chat endpoint with the given model, messages, and options."""
        url = f"{self.host}/api/chat"
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": 4096
            }
        }

        async with self.semaphore:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                try:
                    response = await client.post(url, json=payload)
                    response.raise_for_status()
                    data = response.json()
                    return data["message"]["content"].strip()
                except Exception as e:
                    print(f"[ollama_client] Error calling Ollama: {e}")
                    raise e

    def extract_and_parse_json(self, text: str):
        """
        Extract JSON structures (objects or arrays) from text, repair them if needed,
        and parse them into Python dictionaries or lists.
        """
        # Try direct parsing first
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Try repairing the whole text if it's mostly JSON but has minor errors
        try:
            repaired = json_repair.repair_json(text)
            return json.loads(repaired)
        except Exception:
            pass

        # Find potential JSON blocks (arrays or objects) in the text using bracket scanning
        blocks = []
        
        # Scan for curly braces { }
        brace_count = 0
        start_idx = -1
        for i, char in enumerate(text):
            if char == '{':
                if brace_count == 0:
                    start_idx = i
                brace_count += 1
            elif char == '}':
                if brace_count > 0:
                    brace_count -= 1
                    if brace_count == 0 and start_idx != -1:
                        blocks.append(text[start_idx:i+1])
                        start_idx = -1

        # Scan for square brackets [ ]
        bracket_count = 0
        start_idx = -1
        for i, char in enumerate(text):
            if char == '[':
                if bracket_count == 0:
                    start_idx = i
                bracket_count += 1
            elif char == ']':
                if bracket_count > 0:
                    bracket_count -= 1
                    if bracket_count == 0 and start_idx != -1:
                        blocks.append(text[start_idx:i+1])
                        start_idx = -1

        parsed_items = []
        for block in blocks:
            try:
                repaired = json_repair.repair_json(block)
                parsed = json.loads(repaired)
                if isinstance(parsed, list):
                    parsed_items.extend(parsed)
                elif isinstance(parsed, dict):
                    parsed_items.append(parsed)
            except Exception:
                continue

        if parsed_items:
            # If we collected multiple dictionaries, or list of things, return them.
            # If it's a single item, return it directly.
            if len(parsed_items) == 1:
                return parsed_items[0]
            return parsed_items

        # Fallback regex search for anything inside ```json ... ``` or similar codeblocks
        codeblock_match = re.findall(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
        for block in codeblock_match:
            try:
                repaired = json_repair.repair_json(block)
                return json.loads(repaired)
            except Exception:
                continue

        # If everything fails, raise a parsing error
        raise ValueError(f"Could not extract or repair JSON from: {text[:200]}...")
