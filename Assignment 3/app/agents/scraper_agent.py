from app.orchestrator import build_scraper_prompt
from app.tools.browser_tools import WebPageInspector
from app.tools.mcp_bridge import MCPToolAdapter
from app.tools.groq_client import GroqClient


class ScraperAgent:
    def __init__(self, adapter: MCPToolAdapter | None = None, inspector: WebPageInspector | None = None, client: GroqClient | None = None) -> None:
        self.adapter = adapter or MCPToolAdapter()
        self.inspector = inspector or WebPageInspector()
        self.client = client or GroqClient()
        self.adapter.register("inspect_page", self.inspector.inspect_page)

    def run(self, url: str) -> dict:
        result = self.adapter.call("inspect_page", url=url)
        if result.status != "success":
            raise RuntimeError(result.error or "Scraping failed")

        page_summary = result.data
        prompt = build_scraper_prompt(page_summary)
        insight = self.client.ask(
            prompt,
            system_prompt="You are a web inspection agent. Summarize page content for QA automation.",
            task_name="scraper_inspection",
        )

        return {
            "page_summary": page_summary,
            "groq_insight": insight or "Groq inspection unavailable.",
            "groq_used": insight is not None,
        }
