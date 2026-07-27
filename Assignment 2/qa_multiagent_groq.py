import os
import re
import time
from pathlib import Path
from typing import TypedDict

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langgraph.graph import END, START, StateGraph

load_dotenv()

REQUIREMENTS_PATH = Path(__file__).with_name("qa_requirements.md")

if not os.getenv("GROQ_API_KEY"):
    raise RuntimeError("Set the GROQ_API_KEY environment variable before running this workflow.")

MODEL_CATALOG = {
    "groq/compound": {"input_cost_per_1m": 0.13, "output_cost_per_1m": 0.13},
    "openai/gpt-oss-120b": {"input_cost_per_1m": 0.06, "output_cost_per_1m": 0.06},
    "meta-llama/llama-prompt-guard-2-22m": {"input_cost_per_1m": 0.08, "output_cost_per_1m": 0.08},
}

AGENT_SPECS = {
    "requirements_analyst": {
        "prompt": "You are a senior QA requirements analyst. Identify actors, business rules, acceptance criteria, risks, dependencies, and ambiguities. Be concise and do not invent missing facts.",
        "required_terms": ["actors", "business rules", "acceptance criteria", "risks", "ambiguities"],
    },
    "test_designer": {
        "prompt": "You are a senior test designer. Produce a compact Markdown table with ID, scenario, preconditions, steps, expected result, test type, and priority. Cover positive, negative, boundary, security, and failure paths.",
        "required_terms": ["scenario", "preconditions", "expected result", "priority"],
    },
    "security_reviewer": {
        "prompt": "You are a security reviewer for a QA workflow. Highlight authentication, authorization, replay, token expiry, rate-limit, link reuse, and data exposure risks. If a requirement is missing or contradictory, say exactly what is unclear and what needs a decision.",
        "required_terms": ["rate-limit", "token", "replay", "risk"],
    },
    "performance_reviewer": {
        "prompt": "You are a performance reviewer for a QA workflow. Highlight latency, throughput, rate-limit, retry, timeout, and resilience risks that affect the reset link workflow. If the requirement is vague, call that out clearly.",
        "required_terms": ["latency", "throughput", "timeout", "resilience"],
    },
    "qa_reviewer": {
        "prompt": "You are a critical QA lead. Review the proposed tests, the security findings, and the performance findings for requirement coverage, missing edge cases, duplication, testability, and business risk. Finish with APPROVE or REVISE and a short reason.",
        "required_terms": ["approve", "revise", "coverage", "risk"],
    },
}


class QAAgentState(TypedDict):
    requirement: str
    analysis: str
    test_cases: str
    security_review: str
    performance_review: str
    review: str


def score_output(output: str, required_terms: list[str]) -> float:
    text = (output or "").lower()
    hit_ratio = sum(1 for term in required_terms if term in text) / max(len(required_terms), 1)
    structure_bonus = 1.0 if any(marker in text for marker in ["|", "- ", "1.", "2."]) else 0.0
    return round(hit_ratio * 0.7 + structure_bonus * 0.3, 3)


def estimate_tokens(text: str) -> int:
    return max(1, len(re.findall(r"\S+", text)))


def estimate_cost(model_name: str, prompt_tokens: int, output_tokens: int) -> float:
    pricing = MODEL_CATALOG[model_name]
    input_cost = (prompt_tokens / 1_000_000) * pricing["input_cost_per_1m"]
    output_cost = (output_tokens / 1_000_000) * pricing["output_cost_per_1m"]
    return round(input_cost + output_cost, 6)


def call_specialist(model_name: str, system_prompt: str, task: str) -> tuple[str, float, int, int, str | None]:
    max_tokens = 512 if model_name == "meta-llama/llama-prompt-guard-2-22m" else 1500
    model = ChatGroq(
        model=model_name,
        temperature=0.2,
        max_tokens=max_tokens,
        max_retries=1,
    )
    started = time.perf_counter()
    try:
        if model_name == "meta-llama/llama-prompt-guard-2-22m":
            response = model.invoke([("human", f"{system_prompt}\n\n{task}")])
        else:
            response = model.invoke([
                ("system", system_prompt),
                ("human", task),
            ])
        elapsed = round(time.perf_counter() - started, 3)
        text = getattr(response, "content", str(response))
        if isinstance(text, list):
            text = "\n".join(str(part) for part in text)
        prompt_tokens = estimate_tokens(system_prompt + "\n" + task)
        output_tokens = estimate_tokens(str(text))
        return str(text), elapsed, prompt_tokens, output_tokens, None
    except Exception as exc:
        elapsed = round(time.perf_counter() - started, 3)
        return f"ERROR: {exc}", elapsed, 0, 0, str(exc)


def build_graph(model_by_agent: dict[str, str]):
    def get_model(agent_name: str) -> str:
        return model_by_agent.get(agent_name, next(iter(model_by_agent.values())))

    def requirements_analyst(state: QAAgentState):
        analysis, _, _, _, _ = call_specialist(
            get_model("requirements_analyst"),
            AGENT_SPECS["requirements_analyst"]["prompt"],
            f"Analyze this requirement for testing:\n\n{state['requirement']}",
        )
        return {"analysis": analysis}

    def test_designer(state: QAAgentState):
        test_cases, _, _, _, _ = call_specialist(
            get_model("test_designer"),
            AGENT_SPECS["test_designer"]["prompt"],
            f"Requirement:\n{state['requirement']}\n\nRequirements analysis:\n{state['analysis']}\n\nDesign executable test cases.",
        )
        return {"test_cases": test_cases}

    def security_reviewer(state: QAAgentState):
        security_review, _, _, _, _ = call_specialist(
            get_model("security_reviewer"),
            AGENT_SPECS["security_reviewer"]["prompt"],
            f"Requirement:\n{state['requirement']}\n\nRequirements analysis:\n{state['analysis']}\n\nGenerated test cases:\n{state['test_cases']}",
        )
        return {"security_review": security_review}

    def performance_reviewer(state: QAAgentState):
        performance_review, _, _, _, _ = call_specialist(
            get_model("performance_reviewer"),
            AGENT_SPECS["performance_reviewer"]["prompt"],
            f"Requirement:\n{state['requirement']}\n\nRequirements analysis:\n{state['analysis']}\n\nGenerated test cases:\n{state['test_cases']}\n\nSecurity review:\n{state['security_review']}",
        )
        return {"performance_review": performance_review}

    def qa_reviewer(state: QAAgentState):
        review, _, _, _, _ = call_specialist(
            get_model("qa_reviewer"),
            AGENT_SPECS["qa_reviewer"]["prompt"],
            f"Requirement:\n{state['requirement']}\n\nAnalysis:\n{state['analysis']}\n\nTest cases:\n{state['test_cases']}\n\nSecurity review:\n{state['security_review']}\n\nPerformance review:\n{state['performance_review']}",
        )
        return {"review": review}

    builder = StateGraph(QAAgentState)
    builder.add_node("requirements_analyst", requirements_analyst)
    builder.add_node("test_designer", test_designer)
    builder.add_node("security_reviewer", security_reviewer)
    builder.add_node("performance_reviewer", performance_reviewer)
    builder.add_node("qa_reviewer", qa_reviewer)
    builder.add_edge(START, "requirements_analyst")
    builder.add_edge("requirements_analyst", "test_designer")
    builder.add_edge("test_designer", "security_reviewer")
    builder.add_edge("security_reviewer", "performance_reviewer")
    builder.add_edge("performance_reviewer", "qa_reviewer")
    builder.add_edge("qa_reviewer", END)
    return builder.compile()


def evaluate_model_per_agent(model_name: str, requirement_text: str):
    results = {}
    for agent_name, spec in AGENT_SPECS.items():
        task_text = f"Analyze this requirement for testing:\n\n{requirement_text}" if agent_name == "requirements_analyst" else (
            f"Requirement:\n{requirement_text}\n\nRequirements analysis:\n{results.get('analysis', '')}\n\nDesign executable test cases." if agent_name == "test_designer" else (
                f"Requirement:\n{requirement_text}\n\nRequirements analysis:\n{results.get('analysis', '')}\n\nGenerated test cases:\n{results.get('test_cases', '')}" if agent_name == "security_reviewer" else (
                    f"Requirement:\n{requirement_text}\n\nRequirements analysis:\n{results.get('analysis', '')}\n\nGenerated test cases:\n{results.get('test_cases', '')}\n\nSecurity review:\n{results.get('security_review', '')}" if agent_name == "performance_reviewer" else (
                        f"Requirement:\n{requirement_text}\n\nAnalysis:\n{results.get('analysis', '')}\n\nTest cases:\n{results.get('test_cases', '')}\n\nSecurity review:\n{results.get('security_review', '')}\n\nPerformance review:\n{results.get('performance_review', '')}"
                    )
                )
            )
        )
        output, elapsed, prompt_tokens, output_tokens, error = call_specialist(model_name, spec["prompt"], task_text)
        quality_score = 0.0 if error else score_output(output, spec["required_terms"])
        cost_estimate = 0.0 if error else estimate_cost(model_name, prompt_tokens, output_tokens)
        results[agent_name] = {
            "output": output,
            "quality": quality_score,
            "latency": elapsed,
            "cost": cost_estimate,
            "error": error,
        }
        if agent_name == "requirements_analyst":
            results["analysis"] = output
        elif agent_name == "test_designer":
            results["test_cases"] = output
        elif agent_name == "security_reviewer":
            results["security_review"] = output
        elif agent_name == "performance_reviewer":
            results["performance_review"] = output
        elif agent_name == "qa_reviewer":
            results["review"] = output
    return results


def choose_best_model(requirement_text: str):
    ranking = []
    for model_name in MODEL_CATALOG:
        per_agent_results = evaluate_model_per_agent(model_name, requirement_text)
        agent_scores = {}
        for agent_name, metrics in per_agent_results.items():
            if agent_name not in AGENT_SPECS:
                continue
            quality = metrics["quality"]
            latency = metrics["latency"]
            cost = metrics["cost"]
            latency_score = max(0.0, 1.0 - (latency / 20.0))
            cost_score = max(0.0, 1.0 - (cost / 0.1))
            balanced_score = round((quality * 0.6) + (latency_score * 0.2) + (cost_score * 0.2), 3)
            agent_scores[agent_name] = {"balanced_score": balanced_score, **metrics}
        ranking.append((model_name, agent_scores))
    selected_models = {}
    for agent_name in AGENT_SPECS:
        candidate_scores = []
        for model_name, scores in ranking:
            candidate_scores.append((scores[agent_name]["balanced_score"], model_name, scores[agent_name]))
        best_score, best_model, best_metrics = max(candidate_scores, key=lambda item: item[0])
        selected_models[agent_name] = {"model": best_model, "score": best_score, "metrics": best_metrics}
    return selected_models


def main():
    requirement_text = REQUIREMENTS_PATH.read_text(encoding="utf-8").strip()
    print("Requirements document:")
    print(requirement_text)
    print("\n" + "=" * 60)

    selected_models = choose_best_model(requirement_text)
    print("Best model for each agent:")
    for agent_name, selection in selected_models.items():
        error_note = f" | error={selection['metrics'].get('error')}" if selection['metrics'].get('error') else ""
        print(f"- {agent_name}: {selection['model']} | balanced_score={selection['score']:.3f} | quality={selection['metrics']['quality']:.3f} | latency={selection['metrics']['latency']:.3f}s | cost=${selection['metrics']['cost']:.6f}{error_note}")
    print("\n" + "=" * 60)

    initial_state: QAAgentState = {
        "requirement": requirement_text,
        "analysis": "",
        "test_cases": "",
        "security_review": "",
        "performance_review": "",
        "review": "",
    }

    model_by_agent = {agent_name: selection["model"] for agent_name, selection in selected_models.items()}
    final_chain = build_graph(model_by_agent)
    result = final_chain.invoke(initial_state)

    for heading, key in [
        ("REQUIREMENTS ANALYST", "analysis"),
        ("TEST DESIGNER", "test_cases"),
        ("SECURITY REVIEWER", "security_review"),
        ("PERFORMANCE REVIEWER", "performance_review"),
        ("QA REVIEWER", "review"),
    ]:
        print(f"\n{'=' * 20} {heading} {'=' * 20}\n")
        print(result[key])


if __name__ == "__main__":
    main()
