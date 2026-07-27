from app.orchestrator import build_result_prompt, build_scraper_prompt, build_test_prompt


def test_build_test_prompt_contains_page_context():
    summary = {
        "title": "Example Page",
        "url": "https://example.com",
        "elements": [{"tag": "button", "text": "Submit", "locator": "button.btn"}],
        "key_functionalities": ["Submit button"],
    }

    prompt = build_test_prompt(summary)

    assert "Example Page" in prompt
    assert "https://example.com" in prompt
    assert "Submit button" in prompt
    assert "button.btn" in prompt


def test_build_scraper_prompt_mentions_inspection_task():
    summary = {
        "title": "Example Page",
        "url": "https://example.com",
        "elements": [{"tag": "button", "text": "Submit", "locator": "button.btn"}],
        "key_functionalities": ["Submit button"],
    }

    prompt = build_scraper_prompt(summary)

    assert "scrape" in prompt.lower()
    assert "Example Page" in prompt


def test_build_result_prompt_mentions_execution_summary():
    result = {
        "generated_test_path": "generated_tests/generated_test.py",
        "execution": {"returncode": 0, "stdout": "passed"},
    }

    prompt = build_result_prompt(result)

    assert "generated_test_path" in prompt
    assert "passed" in prompt
