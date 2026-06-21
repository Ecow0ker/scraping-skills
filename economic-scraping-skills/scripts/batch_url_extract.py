#!/usr/bin/env python3
"""Extract a CSV list of URLs into a research dataset."""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from save_raw_response import export_records, parse_formats
from single_page_extract import extract_one, parse_field_specs


def read_urls(path: Path, url_column: str, limit: int | None = None) -> list[str]:
    urls: list[str] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if url_column not in (reader.fieldnames or []):
            raise ValueError(f"URL column '{url_column}' not found in {path}")
        for row in reader:
            url = (row.get(url_column) or "").strip()
            if url:
                urls.append(url)
            if limit and len(urls) >= limit:
                break
    return urls


def main() -> int:
    parser = argparse.ArgumentParser(description="Batch extract URLs from a CSV file.")
    parser.add_argument("input_csv")
    parser.add_argument("--url-column", default="url")
    parser.add_argument("--project-dir", default="research_scrape_output")
    parser.add_argument("--field", action="append", help="Field mapping in name=css_selector format")
    parser.add_argument("--mode", choices=["auto", "static", "dynamic", "stealth"], default="auto")
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--download-delay", type=float, default=10.0)
    parser.add_argument("--formats", default="jsonl,csv")
    parser.add_argument("--stem", default="batch_items")
    args = parser.parse_args()

    fields = parse_field_specs(args.field)
    urls = read_urls(Path(args.input_csv), args.url_column, args.limit)
    records = []
    failures = []
    for index, url in enumerate(urls, start=1):
        try:
            records.append(extract_one(url, args.project_dir, fields, mode=args.mode, timeout=args.timeout))
        except Exception as exc:
            failures.append({"source_url": url, "error": str(exc)})
        if index < len(urls) and args.download_delay > 0:
            time.sleep(args.download_delay)

    if failures:
        records.extend(failures)
    outputs = export_records(records, args.project_dir, args.stem, parse_formats(args.formats))
    print(json.dumps({"requested": len(urls), "records": len(records), "failures": len(failures), "outputs": outputs}, ensure_ascii=False, indent=2))
    return 0 if not failures else 2


if __name__ == "__main__":
    raise SystemExit(main())
