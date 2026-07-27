from app.tools.browser_tools import WebPageInspector


def test_extract_summary_from_html_returns_multiple_locators_and_functionalities():
    inspector = WebPageInspector()
    html = """
    <html>
      <body>
        <h1>Demo Page</h1>
        <form id='login-form'>
          <input name='username' placeholder='Username' />
          <button type='submit'>Login</button>
        </form>
        <a href='/help'>Help</a>
      </body>
    </html>
    """

    summary = inspector.extract_summary_from_html(html, url="https://example.com", title="Demo Page")

    assert summary["title"] == "Demo Page"
    assert len(summary["elements"]) >= 4
    assert any(item["tag"] == "form" for item in summary["elements"])
    assert any(item["tag"] == "input" for item in summary["elements"])
    assert any(item["tag"] == "button" for item in summary["elements"])
    assert "Contains a form" in summary["key_functionalities"]
    assert "Contains buttons" in summary["key_functionalities"]
