#!/usr/bin/env python3
"""Fetch and archive raw web responses for research datasets."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


EXTRACTOR_VERSION = "0.1.1"
DEFAULT_USER_AGENT = "Mozilla/5.0 research-collector/0.1"
SENSITIVE_HEADERS = {"cookie", "set-cookie", "authorization", "proxy-authorization"}

LAYOUTS = {
    "en": {
        "config": ("config",),
        "raw": ("data", "raw"),
        "processed": ("data", "processed"),
        "metadata": ("data", "metadata"),
        "reports": ("reports",),
        "logs": ("logs",),
        "code": ("code",),
    },
    "zh": {
        "config": ("配置文件",),
        "raw": ("数据文件", "原始文件"),
        "processed": ("数据文件", "处理后数据"),
        "metadata": ("数据文件", "元数据"),
        "reports": ("报告文件",),
        "logs": ("日志文件",),
        "code": ("代码文件",),
    },
}


@dataclass
class FetchResult:
    source_url: str
    final_url: str
    status_code: int
    headers: dict[str, str]
    body: bytes
    fetched_at: str
    fetcher_name: str

    @property
    def content_hash(self) -> str:
        return hashlib.sha256(self.body).hexdigest()


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def ensure_project_dirs(project_dir: Path, language: str = "en") -> dict[str, Path]:
    layout = LAYOUTS.get(language, LAYOUTS["en"])
    paths = {
        key: project_dir.joinpath(*parts) for key, parts in layout.items()
    }
    for path in paths.values():
        path.mkdir(parents=True, exist_ok=True)
    return paths


def _headers_to_dict(headers: Any) -> dict[str, str]:
    try:
        return {str(k): str(v) for k, v in dict(headers).items()}
    except Exception:
        return {}


def iri_to_uri(url: str) -> str:
    parts = urllib.parse.urlsplit(url)
    path = urllib.parse.quote(parts.path, safe="/%")
    query = urllib.parse.quote(parts.query, safe="=&?/%:+")
    fragment = urllib.parse.quote(parts.fragment, safe="")
    return urllib.parse.urlunsplit((parts.scheme, parts.netloc, path, query, fragment))


def _fetch_with_urllib(url: str, timeout: int, headers: dict[str, str] | None = None) -> FetchResult:
    request_headers = {"User-Agent": DEFAULT_USER_AGENT}
    if headers:
        request_headers.update(headers)
    request = urllib.request.Request(iri_to_uri(url), headers=request_headers)
    fetched_at = utc_now()
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read()
            return FetchResult(
                source_url=url,
                final_url=response.geturl(),
                status_code=getattr(response, "status", 200),
                headers={k: v for k, v in response.headers.items()},
                body=body,
                fetched_at=fetched_at,
                fetcher_name="urllib",
            )
    except urllib.error.HTTPError as exc:
        body = exc.read()
        return FetchResult(
            source_url=url,
            final_url=exc.geturl(),
            status_code=exc.code,
            headers={k: v for k, v in exc.headers.items()},
            body=body,
            fetched_at=fetched_at,
            fetcher_name="urllib",
        )


def _fetch_with_scrapling_static(url: str, timeout: int, headers: dict[str, str] | None = None) -> FetchResult:
    from scrapling.fetchers import Fetcher

    page = Fetcher.get(url, timeout=timeout, headers=headers or {}, follow_redirects="safe")
    body = page.body if isinstance(page.body, bytes) else bytes(page.body)
    return FetchResult(
        source_url=url,
        final_url=str(getattr(page, "url", url)),
        status_code=int(getattr(page, "status", 0) or 0),
        headers=_headers_to_dict(getattr(page, "headers", {})),
        body=body,
        fetched_at=utc_now(),
        fetcher_name="scrapling.Fetcher",
    )


def _fetch_with_scrapling_browser(
    url: str,
    timeout: int,
    mode: str,
    wait_selector: str | None = None,
    headless: bool = True,
) -> FetchResult:
    if mode == "stealth":
        from scrapling.fetchers import StealthyFetcher as BrowserFetcher

        fetcher_name = "scrapling.StealthyFetcher"
    else:
        from scrapling.fetchers import DynamicFetcher as BrowserFetcher

        fetcher_name = "scrapling.DynamicFetcher"

    kwargs: dict[str, Any] = {
        "timeout": timeout * 1000,
        "headless": headless,
        "network_idle": True,
    }
    if wait_selector:
        kwargs["wait_selector"] = wait_selector
    page = BrowserFetcher.fetch(url, **kwargs)
    body = page.body if isinstance(page.body, bytes) else bytes(page.body)
    return FetchResult(
        source_url=url,
        final_url=str(getattr(page, "url", url)),
        status_code=int(getattr(page, "status", 0) or 0),
        headers=_headers_to_dict(getattr(page, "headers", {})),
        body=body,
        fetched_at=utc_now(),
        fetcher_name=fetcher_name,
    )


def fetch_url(
    url: str,
    timeout: int = 30,
    mode: str = "auto",
    headers: dict[str, str] | None = None,
    wait_selector: str | None = None,
    headless: bool = True,
) -> FetchResult:
    """Fetch a URL. Use Scrapling when available, then fall back to urllib for static pages."""
    if mode in {"dynamic", "stealth"}:
        return _fetch_with_scrapling_browser(url, timeout, mode, wait_selector, headless)

    try:
        return _fetch_with_scrapling_static(url, timeout, headers)
    except Exception:
        if mode == "static":
            raise
        return _fetch_with_urllib(url, timeout, headers)


def guess_extension(headers: dict[str, str]) -> str:
    content_type = ""
    for key, value in headers.items():
        if key.lower() == "content-type":
            content_type = value.lower()
            break
    if "json" in content_type:
        return ".json"
    if "xml" in content_type:
        return ".xml"
    if "text/plain" in content_type:
        return ".txt"
    return ".html"


def redact_headers(headers: dict[str, str]) -> dict[str, str]:
    redacted: dict[str, str] = {}
    for key, value in headers.items():
        if key.lower() in SENSITIVE_HEADERS:
            redacted[key] = "[redacted]"
        else:
            redacted[key] = value
    return redacted


def save_raw_response(result: FetchResult, project_dir: str | Path, language: str = "en") -> dict[str, Any]:
    project_path = Path(project_dir)
    paths = ensure_project_dirs(project_path, language=language)
    stem = f"{result.fetched_at.replace(':', '').replace('+', 'Z')}_{result.content_hash[:16]}"
    raw_path = paths["raw"] / f"{stem}{guess_extension(result.headers)}"
    raw_path.write_bytes(result.body)

    metadata = {
        "source_url": result.source_url,
        "final_url": result.final_url,
        "fetched_at": result.fetched_at,
        "status_code": result.status_code,
        "content_hash": result.content_hash,
        "raw_file_path": str(raw_path),
        "headers": redact_headers(result.headers),
        "extractor_name": result.fetcher_name,
        "extractor_version": EXTRACTOR_VERSION,
    }
    meta_path = paths["metadata"] / f"{stem}.json"
    meta_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    metadata["metadata_file_path"] = str(meta_path)
    return metadata


def flatten_value(value: Any) -> Any:
    if isinstance(value, (str, int, float)) or value is None:
        return value
    if isinstance(value, bool):
        return int(value)
    return json.dumps(value, ensure_ascii=False)


def export_records(
    records: list[dict[str, Any]],
    project_dir: str | Path,
    stem: str,
    formats: list[str],
    language: str = "en",
    final_dir_name: str | None = None,
) -> dict[str, str]:
    paths = ensure_project_dirs(Path(project_dir), language=language)
    output_paths: dict[str, str] = {}
    normalized = [{k: flatten_value(v) for k, v in record.items()} for record in records]

    if "jsonl" in formats:
        path = paths["processed"] / f"{stem}.jsonl"
        with path.open("w", encoding="utf-8") as handle:
            for record in normalized:
                handle.write(json.dumps(record, ensure_ascii=False) + "\n")
        output_paths["jsonl"] = str(path)

    if "csv" in formats:
        path = paths["processed"] / f"{stem}.csv"
        fieldnames = []
        seen_fields: set[str] = set()
        for record in normalized:
            for key in record.keys():
                if key not in seen_fields:
                    fieldnames.append(key)
                    seen_fields.add(key)
        with path.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(normalized)
        output_paths["csv"] = str(path)

    if any(fmt in formats for fmt in {"xlsx", "excel", "dta", "parquet", "duckdb"}):
        try:
            import pandas as pd
        except Exception as exc:
            output_paths["pandas_error"] = f"pandas not available: {exc}"
            return output_paths

        frame = pd.DataFrame(normalized)
        if "xlsx" in formats or "excel" in formats:
            path = paths["processed"] / f"{stem}.xlsx"
            frame.to_excel(path, index=False)
            output_paths["xlsx"] = str(path)
        if "parquet" in formats:
            path = paths["processed"] / f"{stem}.parquet"
            frame.to_parquet(path, index=False)
            output_paths["parquet"] = str(path)
        if "duckdb" in formats:
            try:
                import duckdb
            except Exception as exc:
                output_paths["duckdb_error"] = f"duckdb not available: {exc}"
            else:
                path = paths["processed"] / f"{stem}.duckdb"
                connection = duckdb.connect(str(path))
                try:
                    connection.register("records_frame", frame)
                    connection.execute("CREATE OR REPLACE TABLE records AS SELECT * FROM records_frame")
                finally:
                    connection.close()
                output_paths["duckdb"] = str(path)
        if "dta" in formats:
            path = paths["processed"] / f"{stem}.dta"
            dta_frame, labels = prepare_stata_frame(frame)
            dta_frame.to_stata(path, write_index=False, version=118, variable_labels=labels)
            output_paths["dta"] = str(path)
            labels_path = paths["processed"] / f"{stem}_dta_labels.json"
            labels_path.write_text(json.dumps(labels, ensure_ascii=False, indent=2), encoding="utf-8")
            output_paths["dta_labels"] = str(labels_path)

    if final_dir_name:
        final_dir = Path(project_dir) / final_dir_name
        requested_final_dir = Path(final_dir_name)
        if requested_final_dir.parent != Path(".") or requested_final_dir.is_absolute():
            final_dir = requested_final_dir
        final_dir.mkdir(parents=True, exist_ok=True)
        for fmt, source in list(output_paths.items()):
            if fmt.endswith("_error"):
                continue
            source_path = Path(source)
            if source_path.exists() and source_path.is_file():
                final_path = final_dir / source_path.name
                shutil.copy2(source_path, final_path)
                output_paths[f"final_{fmt}"] = str(final_path)

    return output_paths


def prepare_stata_frame(frame: Any) -> tuple[Any, dict[str, str]]:
    used: set[str] = set()
    rename: dict[str, str] = {}
    labels: dict[str, str] = {}
    for index, column in enumerate(frame.columns, start=1):
        safe = re.sub(r"[^A-Za-z0-9_]", "_", str(column)).strip("_").lower()
        if not safe or not re.match(r"^[A-Za-z_]", safe):
            safe = f"v{index}"
        safe = safe[:28]
        original = safe
        counter = 1
        while safe in used:
            suffix = f"_{counter}"
            safe = f"{original[: 32 - len(suffix)]}{suffix}"
            counter += 1
        used.add(safe)
        rename[column] = safe
        labels[safe] = str(column)[:80]
    return frame.rename(columns=rename), labels


def parse_formats(raw: str) -> list[str]:
    return [part.strip().lower() for part in raw.split(",") if part.strip()]


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch one URL and archive the raw response.")
    parser.add_argument("url")
    parser.add_argument("--project-dir", default="research_scrape_output")
    parser.add_argument("--language", choices=["zh", "en"], default="en")
    parser.add_argument("--mode", choices=["auto", "static", "dynamic", "stealth"], default="auto")
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--wait-selector")
    parser.add_argument("--no-headless", action="store_true")
    parser.add_argument("--formats", default="jsonl,csv")
    args = parser.parse_args()

    result = fetch_url(
        args.url,
        timeout=args.timeout,
        mode=args.mode,
        wait_selector=args.wait_selector,
        headless=not args.no_headless,
    )
    metadata = save_raw_response(result, args.project_dir, language=args.language)
    export_records([metadata], args.project_dir, "raw_responses", parse_formats(args.formats), language=args.language)
    print(json.dumps(metadata, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
