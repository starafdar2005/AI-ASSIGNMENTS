# QA Multi-Agent Groq Workflow

This project implements a LangGraph-based QA multi-agent workflow that reads a requirements document, sends the content through specialist agents, and compares multiple Groq-backed models by quality, latency, and estimated cost.

## Files
- `qa_requirements.md`: sample requirements document used by the workflow.
- `qa_multiagent_groq.py`: runnable implementation of the multi-agent evaluator.

## Run
1. Install required packages:
   `pip install python-dotenv langchain-groq langgraph`
2. Set the Groq API key:
   `set GROQ_API_KEY=your_key`
3. Run:
   `python qa_multiagent_groq.py`
