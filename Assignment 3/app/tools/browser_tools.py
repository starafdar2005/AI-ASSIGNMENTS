import requests
from bs4 import BeautifulSoup


class WebPageInspector:
    def inspect_page(self, url: str) -> dict:
        try:
            from playwright.sync_api import sync_playwright
        except Exception:
            sync_playwright = None

        if sync_playwright is not None:
            try:
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    page = browser.new_page()
                    page.goto(url, wait_until="networkidle", timeout=60000)
                    html = page.content()
                    title = page.title() or "Untitled"
                    browser.close()
                    return self.extract_summary_from_html(html, url=url, title=title)
            except Exception:
                pass

        response = requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
        return self.extract_summary_from_html(response.text, url=url, title=None)

    def extract_summary_from_html(self, html: str, url: str, title: str | None = None) -> dict:
        soup = BeautifulSoup(html, "html.parser")
        page_title = title or self._extract_title(soup)

        tags = ["a", "button", "input", "form", "select", "textarea", "img", "nav", "header", "main", "section", "h1", "h2", "h3", "p"]
        elements = []
        seen = set()

        for tag in tags:
            for idx, element in enumerate(soup.find_all(tag), start=1):
                text = " ".join(element.get_text(" ", strip=True).split())
                if not text and tag in {"input", "img"}:
                    text = element.get("placeholder", "") or element.get("alt", "")

                locator = self._build_locator(element, idx)
                key = (tag, locator, text)
                if key in seen:
                    continue
                seen.add(key)

                attrs = {
                    key_name: element.get(key_name)
                    for key_name in ["id", "class", "name", "type", "href", "placeholder", "aria-label", "role"]
                    if element.get(key_name)
                }

                semantic_hint = self._semantic_hint(element, tag)
                elements.append({
                    "tag": tag,
                    "locator": locator,
                    "text": text,
                    "attrs": attrs,
                    "semantic_hint": semantic_hint,
                })

        elements = sorted(elements, key=lambda item: self._priority(item["tag"]), reverse=True)

        key_functionalities = []
        if any(item["tag"] == "form" for item in elements):
            key_functionalities.append("Contains a form")
        if any(item["tag"] == "input" for item in elements):
            key_functionalities.append("Contains input fields")
        if any(item["tag"] == "button" for item in elements):
            key_functionalities.append("Contains buttons")
        if any(item["tag"] in {"nav", "header", "main", "section"} for item in elements):
            key_functionalities.append("Contains page sections")
        if any("login" in item["text"].lower() for item in elements):
            key_functionalities.append("Likely login flow")
        if any(item["tag"] in {"a", "button"} for item in elements):
            key_functionalities.append("Contains clickable actions")
        if any("form" in item.get("semantic_hint", "").lower() for item in elements):
            key_functionalities.append("Has a multi-field interaction area")
        if any("button" in item.get("semantic_hint", "").lower() or "link" in item.get("semantic_hint", "").lower() for item in elements):
            key_functionalities.append("Has navigation or action links")

        return {
            "title": page_title,
            "url": url,
            "elements": elements[:40],
            "key_functionalities": key_functionalities,
        }

    def _extract_title(self, soup: BeautifulSoup) -> str:
        title_tag = soup.title
        if title_tag and title_tag.string:
            return title_tag.string.strip()
        return "Untitled"

    def _priority(self, tag: str) -> int:
        return {
            "form": 5,
            "input": 5,
            "button": 4,
            "a": 3,
            "select": 3,
            "textarea": 3,
            "nav": 2,
            "header": 2,
            "main": 2,
            "section": 2,
            "h1": 2,
            "h2": 2,
            "h3": 2,
            "p": 1,
            "img": 1,
        }.get(tag, 0)

    def _semantic_hint(self, element, tag: str) -> str:
        text = " ".join(element.get_text(" ", strip=True).split()).lower()
        if tag == "form":
            return "form"
        if tag == "button":
            return "button"
        if tag == "a":
            return "link"
        if tag == "input":
            return "input"
        if tag in {"nav", "header", "main", "section"}:
            return "page-section"
        if tag in {"h1", "h2", "h3"}:
            return "heading"
        if tag == "img" and text:
            return "image"
        return tag

    def _build_locator(self, element, index: int) -> str:
        element_id = element.get("id")
        if element_id:
            return f"#{element_id}"

        name = element.get("name")
        if name:
            return f"[name='{name}']"

        classes = element.get("class", [])
        if classes:
            return f".{classes[0]}"

        if element.name and element.name.lower() in {"h1", "h2", "h3", "p", "a", "button", "input", "form", "img"}:
            return element.name.lower()

        return f"{element.name or 'tag'}[{index}]"
