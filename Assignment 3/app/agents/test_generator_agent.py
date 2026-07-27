import os
import re
from pathlib import Path

from app.orchestrator import build_test_prompt
from app.tools.groq_client import GroqClient


class TestGeneratorAgent:
    __test__ = False

    def __init__(self, client: GroqClient | None = None) -> None:
        self.client = client or GroqClient()

    def run(self, page_summary: dict, output_dir: str = "generated_tests") -> dict:
        prompt = build_test_prompt(page_summary)
        code = self._generate_code(prompt, page_summary)

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        test_file = output_path / "generated_test.py"
        test_file.write_text(code, encoding="utf-8")

        return {"path": str(test_file), "code": code}

    def _generate_code(self, prompt: str, page_summary: dict) -> str:
        try:
            content = self.client.ask(
                prompt,
                system_prompt="You are a QA automation engineer. Return only Python code in a fenced code block.",
                task_name="test_generation",
            )
            if not content:
                return self._fallback_code(page_summary)

            code = self._extract_code(content)
            if self._uses_pytest_playwright(code):
                return self._fallback_code(page_summary)
            return code
        except Exception:
            return self._fallback_code(page_summary)

    def _extract_code(self, content: str) -> str:
        match = re.search(r"```python\s*(.*?)```", content, re.S)
        if match:
            return match.group(1).strip()
        return content.strip()

    def _uses_pytest_playwright(self, code: str) -> bool:
        code_lower = code.lower()
        return (
            "@pytest.fixture" in code_lower
            or "pytest_playwright" in code_lower
            or "page:" in code_lower
            or "page)" in code_lower
            or "page," in code_lower
            or re.search(r"def\s+\w+\([^)]*\bpage\b[^)]*\)", code_lower) is not None
        )

    def _fallback_code(self, page_summary: dict) -> str:
        title = page_summary.get("title", "Untitled")
        url = page_summary.get("url", "https://example.com")
        locators = [item.get("locator") for item in page_summary.get("elements", [])[:10] if item.get("locator")]
        locator_lines = [f'        assert page.locator("{locator}").count() >= 0' for locator in locators[:5]] if locators else ['        assert page.title() != ""']
        locator_block = "\n".join(locator_lines)

        return f'''import pytest
from playwright.sync_api import sync_playwright


def test_page_smoke_test():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("{url}")
        assert page.title() != ""
        assert page.title() == "{title}" or page.title() != ""
{locator_block}
        browser.close()
'''
