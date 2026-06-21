# Aqistudy Air Quality

Use `scripts/aqistudy_extract.py` for aqistudy history pages.

Also read `references/aqistudy-rules-fragment.md` for the compact routing, folder, report, and low-tech rerun rules.

## Recipe Status

Status: `Beta`. The recipe has been tested on city-day AQI data and produces observation-level CSV, JSONL, and Stata DTA files, but aqistudy may change its page script or API wrapper. If extraction fails, archive the raw page and response first, then inspect the page script before changing the output schema.

## What The Crawl Learned

- The visible month and day pages are useful evidence and contain city/month navigation.
- The actual day-level observations come from `api/historyapi.php` with method `GETDAYDATA`.
- One API response can produce many city-day rows, so repeated raw `content_hash` values are normal.
- The final CSV/DTA must contain observation rows, not page text.

## Output Contract

Each run creates two sibling folders under `--output-parent`. In normal skill use, pass the current workspace root as `--output-parent` so these folders appear directly under the root, not inside a task wrapper folder:

```text
aqistudy数据抓取/
├── 配置文件/
├── 数据文件/
│   ├── 原始文件/
│   ├── 处理后数据/
│   └── 元数据/
├── 报告文件/
│   └── 审查报告.md
├── 日志文件/
└── 代码文件/
    ├── 一键运行.py
    └── 运行方式.md
aqistudy最终数据/
└── final CSV/JSONL/DTA copied from processed outputs
```

English mode uses the same roles with `aqistudy-data/`, `config/`, `data/raw/`, `data/processed/`, `data/metadata/`, `reports/quality_report.md`, `logs/`, `code/`, and `aqistudy-final-data/`.

## Defaults

- Chinese request: pass `--language zh`; use sibling folders `aqistudy数据抓取/` and `aqistudy最终数据/`, Chinese subfolders, and Chinese column names.
- English request: pass `--language en`; use sibling folders `aqistudy-data/` and `aqistudy-final-data/`, English subfolders, and English column names.
- Version suffixes are run-count based. First run has no suffix; second run is `V2` in Chinese or `-v2` in English; third run is `V3` or `-v3`.
- Prefer `--output-parent .` from the workspace root over `--project-dir` so the script can create both sibling folders directly under the root.
- The crawl folder must include a low-tech rerun bundle. Chinese users should see `代码文件/运行方式.md` with the no-parameter command `python 代码文件/一键运行.py`.
- If fields are unspecified, collect city, month, date, AQI, quality level, PM2.5, PM10, SO2, NO2, CO, and O3.
- If fields are specified, keep only those data fields plus required provenance fields.
- Default formats are CSV, JSONL, and Stata DTA. DTA uses safe ASCII variable names and writes a `_dta_labels.json` sidecar so Chinese field labels remain visible.

## Example Commands

```bash
python scripts/aqistudy_extract.py --language zh --output-parent . --max-cities 3 --month latest
python scripts/aqistudy_extract.py --language en --output-parent . --cities 北京,上海 --month 202606 --columns city,date,aqi,pm2_5
```

Use `--version V2` only when the user explicitly asks to force a run label. Otherwise leave `--version auto`.

## QA Gate

Before presenting results:

- Open the final CSV header and confirm it is data-oriented, not page-oriented.
- Confirm the final folder contains `.dta` and `_dta_labels.json` unless the user explicitly disabled DTA output.
- Confirm Chinese requests use Chinese data and provenance column names; English requests use English names.
- Confirm `审查报告.md` exists and is Chinese for Chinese requests; confirm `quality_report.md` exists and is English for English requests.
- Treat repeated `content_hash` values as normal when one API response yields many city-day rows; check `entity_id` for true duplicate observations.
- Report the final data folder first, then the evidence/raw folder.
