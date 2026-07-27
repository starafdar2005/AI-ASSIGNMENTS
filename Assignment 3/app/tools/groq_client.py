import os
from pathlib import Path

import requests
from dotenv import load_dotenv


class GroqClient:
    def __init__(self) -> None:
        self.project_root = Path(__file__).resolve().parents[1]
        load_dotenv(self.project_root / ".env")

    def ask(self, prompt: str, *, system_prompt: str, task_name: str) -> str | None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            return None

        payload = {
            "model": os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"),
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
        }
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=90,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        return content.strip() if content else None
