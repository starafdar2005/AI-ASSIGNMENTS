from app.tools.groq_client import GroqClient


class ResultAgent:
    def __init__(self, client: GroqClient | None = None) -> None:
        self.client = client or GroqClient()

    def run(self, result: dict) -> dict:
        prompt = (
            f"Summarize this automation run.\n"
            f"Generated test file: {result.get('generated_test_path', 'unknown')}\n"
            f"Execution return code: {result.get('execution', {}).get('returncode', 'unknown')}\n"
            f"Execution output: {result.get('execution', {}).get('stdout', '')[:400]}"
        )
        response = self.client.ask(
            prompt,
            system_prompt="You are a QA automation reporting assistant. Return a concise summary of the run.",
            task_name="result_summary",
        )

        return {
            "summary": response or "Automation run completed.",
            "groq_used": response is not None,
        }
