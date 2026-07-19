# Quality Checks

Run quality checks after every collection.

## Required Checks

- total record count
- duplicate count by `content_hash`, `source_url`, or `entity_id` when available
- missing rate for each field
- HTTP status code distribution
- failed request count
- raw file existence
- extraction error count

## Research Data Checks

- Row unit: confirm that one row represents the intended observation, not a whole page dump.
- Price fields: parseability, negative values, extreme outliers, currency/unit changes.
- Date fields: parseability, future dates, unexpected old dates.
- Region fields: missing city/province, inconsistent names.
- Panel fields: duplicate `entity_id` and `observed_at`, missing waves, sudden coverage drops.
- Text fields: empty titles, boilerplate-only text, captcha or access-denied text.

## Delivery Checks

- Final data folder exists separately from the crawl/evidence folder.
- Final CSV/JSONL/DTA/XLSX/Parquet/DuckDB files use the user's language for researcher-facing columns.
- DTA outputs include a sidecar label JSON when column names must be converted to Stata-safe ASCII.
- Raw files, metadata, logs, and the review report are present in the crawl/evidence folder.
- Reusable code folders include a no-parameter run instruction when the task is meant to be rerun.

## Report Style

Reports should be concise and decision-oriented:

- what was collected
- what failed
- which fields look unreliable
- whether another fetch mode or human interaction is needed

Use localized filenames and body text:

- Chinese request: `审查报告.md`, written in Chinese.
- English request: `quality_report.md`, written in English.
