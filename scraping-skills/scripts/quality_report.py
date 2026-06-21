#!/usr/bin/env python3
"""Generate a concise data review report for scraped outputs."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any


def load_records(path: Path) -> list[dict[str, Any]]:
    if path.suffix.lower() == ".jsonl":
        records = []
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    records.append(json.loads(line))
        return records
    if path.suffix.lower() == ".csv":
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            return list(csv.DictReader(handle))
    raise ValueError(f"Unsupported input format: {path.suffix}")


def missing_count(records: list[dict[str, Any]], field: str) -> int:
    count = 0
    for record in records:
        value = record.get(field)
        if value is None or value == "" or value == []:
            count += 1
    return count


def first_value(record: dict[str, Any], fields: list[str]) -> Any:
    for field in fields:
        value = record.get(field)
        if value not in (None, ""):
            return value
    return ""


ZH_HINT_FIELDS = {
    "实体ID",
    "城市",
    "月份",
    "日期",
    "质量等级",
    "状态码",
    "内容哈希",
    "来源网址",
}


def detect_language(records: list[dict[str, Any]], source_path: Path, requested: str = "auto") -> str:
    if requested in {"zh", "en"}:
        return requested
    fields = {key for record in records for key in record.keys()}
    if fields.intersection(ZH_HINT_FIELDS):
        return "zh"
    if any(part in {"报告文件", "数据文件", "处理后数据", "aqistudy最终数据"} for part in source_path.parts):
        return "zh"
    return "en"


def report_file_name(language: str) -> str:
    return "审查报告.md" if language == "zh" else "quality_report.md"


def default_report_path(source_path: Path, language: str) -> Path:
    report_dir_name = "报告文件" if language == "zh" else "reports"
    for parent in source_path.parents:
        if (parent / report_dir_name).exists():
            return parent / report_dir_name / report_file_name(language)
    processed_names = {"处理后数据", "processed"}
    for parent in source_path.parents:
        if parent.name in processed_names and len(parent.parents) >= 2:
            project_root = parent.parents[1]
            return project_root / report_dir_name / report_file_name(language)
    return Path(report_file_name(language))


def write_report(records: list[dict[str, Any]], output_path: Path, source_path: Path, language: str = "en") -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fields = sorted({key for record in records for key in record.keys()})
    status_counts = Counter(str(first_value(record, ["status_code", "状态码"])) for record in records)
    hashes = [first_value(record, ["content_hash", "内容哈希"]) for record in records if first_value(record, ["content_hash", "内容哈希"])]
    shared_hash_rows = sum(count - 1 for count in Counter(hashes).values() if count > 1)
    entity_ids = [first_value(record, ["entity_id", "实体ID"]) for record in records if first_value(record, ["entity_id", "实体ID"])]
    duplicate_entity_ids = sum(count - 1 for count in Counter(entity_ids).values() if count > 1)
    error_records = [
        record
        for record in records
        if first_value(record, ["error", "错误", "extraction_errors", "抽取错误"])
    ]

    if language == "zh":
        lines = [
            "# 审查报告",
            "",
            f"- 数据文件：`{source_path}`",
            f"- 记录数：{len(records)}",
            f"- 字段数：{len(fields)}",
            f"- 重复实体ID：{duplicate_entity_ids}",
            f"- 共用原始内容哈希的行数：{shared_hash_rows}",
            f"- 含错误记录数：{len(error_records)}",
            "",
            "## 状态码",
            "",
        ]
    else:
        lines = [
            "# Quality Report",
            "",
            f"- Source file: `{source_path}`",
            f"- Records: {len(records)}",
            f"- Fields: {len(fields)}",
            f"- Duplicate entity IDs: {duplicate_entity_ids}",
            f"- Rows sharing raw content hashes: {shared_hash_rows}",
            f"- Records with errors: {len(error_records)}",
            "",
            "## Status Codes",
            "",
        ]
    if status_counts:
        for status, count in sorted(status_counts.items()):
            missing_label = "缺失" if language == "zh" else "missing"
            lines.append(f"- `{status or missing_label}`: {count}")
    else:
        lines.append("- 未发现状态码" if language == "zh" else "- No status codes found")

    lines.extend(["", "## 缺失值" if language == "zh" else "## Missing Values", ""])
    for field in fields:
        missing = missing_count(records, field)
        rate = (missing / len(records) * 100) if records else 0
        if language == "zh":
            lines.append(f"- `{field}`：缺失 {missing} 个（{rate:.1f}%）")
        else:
            lines.append(f"- `{field}`: {missing} missing ({rate:.1f}%)")

    lines.extend(["", "## 说明" if language == "zh" else "## Notes", ""])
    if error_records:
        lines.append("- 分析前请先检查含 `错误`、`error` 或 `extraction_errors` 的记录。" if language == "zh" else "- Review records with `error` or `extraction_errors` before analysis.")
    if duplicate_entity_ids:
        lines.append("- 面板或截面分析前，请检查重复的 `实体ID` / `entity_id`。" if language == "zh" else "- Duplicate `entity_id` values need review before panel or cross-sectional analysis.")
    if shared_hash_rows:
        lines.append("- 多行共用同一个原始内容哈希可能是正常情况，例如一个接口响应生成多条城市-日期观测。" if language == "zh" else "- Shared raw content hashes can be normal when one API/listing response yields multiple observation rows.")
    if not records:
        lines.append("- 未发现记录；请重新抓取或检查失败请求。" if language == "zh" else "- No records were found; rerun collection or inspect failed requests.")
    if records and not error_records and not duplicate_entity_ids:
        lines.append("- 基础检查未发现明显结构性质量问题。" if language == "zh" else "- No obvious structural quality issue detected by the basic checks.")

    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a data review report for JSONL or CSV data.")
    parser.add_argument("input_file")
    parser.add_argument("--output", default=None)
    parser.add_argument("--language", choices=["auto", "zh", "en"], default="auto")
    args = parser.parse_args()

    source_path = Path(args.input_file)
    records = load_records(source_path)
    language = detect_language(records, source_path, args.language)
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = default_report_path(source_path, language)
    write_report(records, output_path, source_path, language=language)
    print(json.dumps({"records": len(records), "report": str(output_path)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
