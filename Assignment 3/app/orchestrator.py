import argparse
import json
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:  # pragma: no cover - fallback for minimal environments
    def load_dotenv() -> bool:
        return False


load_dotenv(Path(__file__).resolve().parents[1] / ".env")


def build_scraper_prompt(summary: dict) -> str:
    title = summary.get("title", "Untitled")
    url = summary.get("url", "https://example.com")
    elements = summary.get("elements", [])
    functionalities = ", ".join(summary.get("key_functionalities", [])) or "No special functionality detected"
    locator_text = ", ".join([item.get("locator") for item in elements[:10] if item.get("locator")]) or "No locators detected"

    return (
        f"You are a web scraping agent. Scrape and analyze this page for QA automation.\n"
        f"Page title: {title}\n"
        f"Page URL: {url}\n"
        f"Key functionality: {functionalities}\n"
        f"Important locators: {locator_text}\n"
        "Return a short actionable inspection summary for test generation."
    )


def build_test_prompt(summary: dict) -> str:
    title = summary.get("title", "Untitled")
    url = summary.get("url", "https://example.com")
    locators = [item.get("locator") for item in summary.get("elements", [])[:12] if item.get("locator")]
    functionalities = ", ".join(summary.get("key_functionalities", [])) or "No special functionality detected"
    locator_text = ", ".join(locators) if locators else "No locators detected"

    return (
        f"You are a QA automation engineer. Create a Python pytest + Playwright test file for this webpage.\n"
        f"Page title: {title}\n"
        f"Page URL: {url}\n"
        f"Key functionality: {functionalities}\n"
        f"Use at least 4 of these locators when possible: {locator_text}\n"
        "Return only Python code inside a fenced code block."
    )


def build_result_prompt(result: dict) -> str:
    return (
        f"Summarize this automation run.\n"
        f"generated_test_path: {result.get('generated_test_path', 'unknown')}\n"
        f"Execution return code: {result.get('execution', {}).get('returncode', 'unknown')}\n"
        f"Execution output: {result.get('execution', {}).get('stdout', '')[:400]}"
    )


def build_structured_report(page_summary: dict, generated_test_path: str, execution: dict, final_report: dict) -> dict:
    locator_count = len(page_summary.get("elements", []))
    functionality_count = len(page_summary.get("key_functionalities", []))

    return {
        "summary": {
            "page_title": page_summary.get("title", "Untitled"),
            "page_url": page_summary.get("url", ""),
            "locator_count": locator_count,
            "functionality_count": functionality_count,
        },
        "test_cases": [
            {
                "name": "Page load and title check",
                "status": "passed" if execution.get("returncode") == 0 else "failed",
            },
            {
                "name": "Locator extraction",
                "status": "passed" if locator_count >= 4 else "failed",
            },
            {
                "name": "Functionality detection",
                "status": "passed" if functionality_count >= 1 else "failed",
            },
            {
                "name": "Groq-assisted generation and reporting",
                "status": "passed" if final_report.get("groq_used", False) else "failed",
            },
        ],
        "generated_test_path": generated_test_path,
        "execution_return_code": execution.get("returncode"),
        "groq_used": final_report.get("groq_used", False),
    }


def run_pipeline(url: str, output_dir: str | None = None) -> dict:
    from app.agents.executor_agent import ExecutorAgent
    from app.agents.result_agent import ResultAgent
    from app.agents.scraper_agent import ScraperAgent
    from app.agents.test_generator_agent import TestGeneratorAgent

    scraper = ScraperAgent()
    scraper_result = scraper.run(url)
    page_summary = scraper_result.get("page_summary", scraper_result)

    generator = TestGeneratorAgent()
    generated_test = generator.run(page_summary, output_dir or os.getenv("OUTPUT_DIR", "generated_tests"))

    executor = ExecutorAgent()
    execution = executor.run(generated_test["path"])

    final_result = {
        "page_summary": page_summary,
        "generated_test_path": generated_test["path"],
        "execution": execution,
    }

    result_agent = ResultAgent()
    final_report = result_agent.run(final_result)
    structured_report = build_structured_report(page_summary, generated_test["path"], execution, final_report)

    return {
        **final_result,
        "final_report": final_report,
        "structured_report": structured_report,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the AI multi-agent webpage testing workflow")
    parser.add_argument("--url", default=os.getenv("TARGET_URL", "https://example.com"), help="The webpage URL to inspect")
    parser.add_argument("--output-dir", default=os.getenv("OUTPUT_DIR", "generated_tests"), help="Directory to store the generated test")
    args = parser.parse_args()

    result = run_pipeline(args.url, args.output_dir)
    print(json.dumps(result, indent=2))
