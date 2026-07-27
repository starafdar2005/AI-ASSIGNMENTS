# Assignment 3 - AI Webpage Testing Automation Framework

This project is a complete starter framework for your assignment. It shows how an AI-powered multi-agent system can inspect a webpage, extract locators and key functionality, generate a test file, and execute it.

## What your tutor wants you to learn

Your tutor is likely testing whether you can understand and build a practical AI automation workflow with these ideas:

1. Multi-agent orchestration
   - A controller agent coordinates a scraper, a test generator, and an execution agent.

2. Agentic tooling
   - Agents should rely on tools rather than hard-coded logic. The framework uses a small MCP-style adapter so each agent can call tools.

3. LLM-driven automation
   - The system uses Groq as the reasoning engine to create test code from webpage inspection data.

4. DevOps pipeline integration
   - The project includes an Azure DevOps pipeline file so the automation can run on every push.

5. End-to-end delivery
   - The solution includes code, tests, setup instructions, and a pipeline definition so it is assignment-ready.

## Architecture

The flow is:

1. Scraper agent inspects the target URL.
2. The orchestrator sends the inspection summary to the test generator agent.
3. The test generator agent creates a pytest + Playwright test file.
4. The executor agent runs the test file.
5. The orchestrator returns the final result.

## Project files

- [app/orchestrator.py](app/orchestrator.py) - main controller for the pipeline.
- [app/agents/scraper_agent.py](app/agents/scraper_agent.py) - inspects the webpage and extracts locators.
- [app/agents/test_generator_agent.py](app/agents/test_generator_agent.py) - creates a test file with Groq.
- [app/agents/executor_agent.py](app/agents/executor_agent.py) - runs the generated test file.
- [app/tools/browser_tools.py](app/tools/browser_tools.py) - webpage scraping and locator extraction.
- [app/tools/mcp_bridge.py](app/tools/mcp_bridge.py) - lightweight MCP-style tool interface.
- [azure-pipelines.yml](azure-pipelines.yml) - Azure DevOps pipeline definition.
- [docs/azure-devops-flow.svg](docs/azure-devops-flow.svg) - screenshot-style diagram for your assignment report.

## Setup

1. Create and activate a Python virtual environment.
2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Create a local environment file:

   ```bash
   copy .env.example .env
   ```

4. Put your Groq API key in the .env file.

## Run the pipeline

```bash
python main.py --url https://example.com
```

You can also set the URL in the environment file and run:

```bash
python main.py
```

## Azure DevOps integration

This repository already contains [azure-pipelines.yml](azure-pipelines.yml). To connect it to Azure DevOps:

1. Create a GitHub repository.
2. Push the project to GitHub.
3. In Azure DevOps, create a new Pipeline and connect it to the GitHub repository.
4. Select the repository and the YAML file.
5. Add pipeline variables:
   - GROQ_API_KEY
   - TARGET_URL

## Assignment tips

- Use the generated test file as evidence in your report.
- Include the architecture diagram from [docs/azure-devops-flow.svg](docs/azure-devops-flow.svg).
- Show the flow from scraper to test generator to executor.
- Mention that the project is designed to be extended with real MCP servers later if your tutor wants deeper agentic behavior.
