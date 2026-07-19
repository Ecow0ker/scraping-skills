#!/usr/bin/env python3
"""Extract a single web page into research-ready files."""

from __future__ import annotations

import argparse
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from save_raw_response import export_records, fetch_url, parse_formats, save_raw_response


class SimpleTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._skip = 0
        self._in_title = False
        self.title_parts: list[str] = []
        self.text_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "noscript", "svg"}:
            self._skip += 1
        if tag == "title":
            self._in_title = True

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript", "svg"} and self._skip:
            self._skip -= 1
        if tag == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        text = re.sub(r"\s+", " ", data).strip()
        if not text:
            return
        if self._in_title:
            self.title_parts.append(text)
        if not self._skip:
            self.text_parts.append(text)

    @property
    def title(self) -> str:
        return " ".join(self.title_parts).strip()

    @property
    def text(self) -> str:
        return "\n".join(self.text_parts).strip()


def parse_field_specs(raw_fields: list[str] | None) -> dict[str, str]:
    fields: dict[str, str] = {}
    for raw in raw_fields or []:
        if "=" not in raw:
            raise ValueError(f"Field must use name=selector format: {raw}")
        name, selector = raw.split("=", 1)
        name = name.strip()
        selector = selector.strip()
        if not name or not selector:
            raise ValueError(f"Invalid field spec: {raw}")
        fields[name] = selector
    return fields


def _fallback_extract(html: str, fields: dict[str, str]) -> tuple[dict[str, Any], list[str]]:
    parser = SimpleTextParser()
    parser.feed(html)
    if not fields:
        return {"标题": parser.title, "正文": parser.text}, []

    errors: list[str] = []
    extracted: dict[str, Any] = {}
    for name, selector in fields.items():
        normalized = selector.strip().lower()
        if normalized in {"title", "title::text"}:
            extracted[name] = parser.title
        elif normalized in {"body", "body::text", "text", "全文", "正文"}:
            extracted[name] = parser.text
        else:
            extracted[name] = ""
            errors.append(f"fallback parser cannot evaluate selector for {name}: {selector}")
    return extracted, errors


def extract_fields(html: str, fields: dict[str, str]) -> tuple[dict[str, Any], list[str]]:
    try:
        from scrapling.parser import Selector

        page = Selector(html)
        if not fields:
            return {
                "标题": page.css("title::text").get("") if page.css("title::text") else "",
                "正文": page.get_all_text(ignore_tags=("script", "style", "noscript", "svg")),
            }, []
        extracted: dict[str, Any] = {}
        errors: list[str] = []
        for name, selector in fields.items():
            try:
                values = page.css(selector).getall()
                extracted[name] = values[0] if len(values) == 1 else values
            except Exception as exc:
                extracted[name] = ""
                errors.append(f"{name}: {exc}")
        return extracted, errors
    except Exception:
        return _fallback_extract(html, fields)


def decode_body(body: bytes, headers: dict[str, str] | None = None) -> str:
    header_text = " ".join(f"{k}: {v}" for k, v in (headers or {}).items())
    candidates: list[str] = []
    header_match = re.search(r"charset=([A-Za-z0-9_\\-]+)", header_text, flags=re.I)
    if header_match:
        candidates.append(header_match.group(1))
    preview = body[:4096].decode("ascii", errors="ignore")
    meta_match = re.search(r"charset=[\"']?([A-Za-z0-9_\\-]+)", preview, flags=re.I)
    if meta_match:
        candidates.append(meta_match.group(1))
    candidates.extend(["utf-8", "gb18030"])
    seen: set[str] = set()
    for encoding in candidates:
        normalized = encoding.lower()
        if normalized in seen:
            continue
        seen.add(normalized)
        try:
            return body.decode(encoding)
        except Exception:
            continue
    return body.decode("utf-8", errors="replace")


def extract_one(
    url: str,
    project_dir: str | Path,
    fields: dict[str, str] | None = None,
    mode: str = "auto",
    timeout: int = 30,
    wait_selector: str | None = None,
    headless: bool = True,
    headers: dict[str, str] | None = None,
    language: str = "en",
) -> dict[str, Any]:
    result = fetch_url(url, timeout=timeout, mode=mode, wait_selector=wait_selector, headless=headless, headers=headers)
    metadata = save_raw_response(result, project_dir, language=language)
    html = decode_body(result.body, result.headers)
    extracted, errors = extract_fields(html, fields or {})
    if not result.body:
        errors.append("empty response body")
    record = dict(metadata)
    record.update(extracted)
    if errors:
        record["extraction_errors"] = errors
    return record


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract one page for a research dataset.")
    parser.add_argument("url")
    parser.add_argument("--project-dir", default="research_scrape_output")
    parser.add_argument("--language", choices=["zh", "en"], default="en")
    parser.add_argument("--field", action="append", help="Field mapping in name=css_selector format")
    parser.add_argument("--mode", choices=["auto", "static", "dynamic", "stealth"], default="auto")
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--wait-selector")
    parser.add_argument("--no-headless", action="store_true")
    parser.add_argument("--formats", default="jsonl,csv")
    parser.add_argument("--stem", default="single_page_items")
    args = parser.parse_args()

    fields = parse_field_specs(args.field)
    record = extract_one(
        args.url,
        args.project_dir,
        fields,
        mode=args.mode,
        timeout=args.timeout,
        wait_selector=args.wait_selector,
        headless=not args.no_headless,
        language=args.language,
    )
    outputs = export_records([record], args.project_dir, args.stem, parse_formats(args.formats), language=args.language)
    print(json.dumps({"records": 1, "outputs": outputs, "sample": record}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
