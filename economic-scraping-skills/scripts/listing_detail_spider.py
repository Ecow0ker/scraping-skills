#!/usr/bin/env python3
"""Collect detail pages discovered from a listing page."""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from save_raw_response import export_records, fetch_url, parse_formats, save_raw_response
from single_page_extract import extract_one, parse_field_specs


def discover_links(html: str, base_url: str, selector: str, max_links: int) -> list[str]:
    links: list[str] = []
    try:
        from scrapling.parser import Selector

        page = Selector(html)
        values = page.css(selector).getall()
        links = [urljoin(base_url, value.strip()) for value in values if value and value.strip()]
    except Exception:
        links = [urljoin(base_url, match) for match in re.findall(r"href=[\"']([^\"']+)[\"']", html, flags=re.I)]

    deduped: list[str] = []
    seen: set[str] = set()
    for link in links:
        if link not in seen:
            seen.add(link)
            deduped.append(link)
        if len(deduped) >= max_links:
            break
    return deduped


def filter_links(links: list[str], allow_regex: str | None, deny_regex: str | None) -> list[str]:
    allowed = re.compile(allow_regex) if allow_regex else None
    denied = re.compile(deny_regex) if deny_regex else None
    filtered = []
    for link in links:
        if allowed and not allowed.search(link):
            continue
        if denied and denied.search(link):
            continue
        filtered.append(link)
    return filtered


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect detail pages linked from a listing page.")
    parser.add_argument("start_url")
    parser.add_argument("--project-dir", default="research_scrape_output")
    parser.add_argument("--link-selector", default="a::attr(href)")
    parser.add_argument("--allow-regex")
    parser.add_argument("--deny-regex")
    parser.add_argument("--max-details", type=int, default=20)
    parser.add_argument("--field", action="append", help="Detail field mapping in name=css_selector format")
    parser.add_argument("--mode", choices=["auto", "static", "dynamic", "stealth"], default="auto")
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--download-delay", type=float, default=10.0)
    parser.add_argument("--formats", default="jsonl,csv")
    parser.add_argument("--stem", default="listing_detail_items")
    args = parser.parse_args()

    listing = fetch_url(args.start_url, timeout=args.timeout, mode=args.mode)
    listing_meta = save_raw_response(listing, args.project_dir)
    html = listing.body.decode("utf-8", errors="replace")
    links = discover_links(html, listing.final_url, args.link_selector, args.max_details)
    links = filter_links(links, args.allow_regex, args.deny_regex)
    fields = parse_field_specs(args.field)

    records: list[dict[str, Any]] = []
    failures: list[dict[str, str]] = []
    for index, link in enumerate(links, start=1):
        try:
            record = extract_one(
                link,
                args.project_dir,
                fields,
                mode=args.mode,
                timeout=args.timeout,
                headers={"Referer": listing.final_url},
            )
            record["listing_url"] = args.start_url
            record["listing_content_hash"] = listing_meta["content_hash"]
            records.append(record)
        except Exception as exc:
            failures.append({"source_url": link, "listing_url": args.start_url, "error": str(exc)})
        if index < len(links) and args.download_delay > 0:
            time.sleep(args.download_delay)

    if failures:
        records.extend(failures)
    outputs = export_records(records, args.project_dir, args.stem, parse_formats(args.formats))
    print(json.dumps({"listing_url": args.start_url, "discovered": len(links), "records": len(records), "failures": len(failures), "outputs": outputs}, ensure_ascii=False, indent=2))
    return 0 if not failures else 2


if __name__ == "__main__":
    raise SystemExit(main())
