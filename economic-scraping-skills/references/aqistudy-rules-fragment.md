# Aqistudy Rules Fragment

Load this fragment when the request mentions aqistudy, `https://www.aqistudy.cn/historydata/index.php`, AQI, air quality, hot cities, or current-month China city air-quality history.

## Routing

- If the user asks in Chinese, use `--language zh`.
- If the prompt is like "请爬取 https://www.aqistudy.cn/historydata/index.php 中热门城市这个月的空气质量", do not ask for more fields. Treat it as hot cities plus latest available month.
- Do not limit hot cities unless the user explicitly asks for a sample or maximum count.
- Prefer the aqistudy source-specific extractor over generic page scraping because the research dataset is city-day observations, not page text.

## Data Contract

- Default rows: one city-day observation per row.
- Default data columns: city, month, date, AQI, quality level, PM2.5, PM10, SO2, NO2, CO, O3, rank, and data status.
- Default output formats: CSV, JSONL, and Stata DTA. Keep `_dta_labels.json` beside the DTA file so Chinese column labels remain inspectable.
- If the user specifies fields, keep those fields first and still append provenance columns.
- Chinese requests must output Chinese column names; English requests must output English column names.

## Folder And Report Contract

- Create sibling folders under the output parent. In normal skill use, the output parent is the current workspace/project root.
- Chinese first run: `aqistudy数据抓取/` and `aqistudy最终数据/`.
- Chinese second run: `aqistudy数据抓取V2/` and `aqistudy最终数据V2/`.
- English first run: `aqistudy-data/` and `aqistudy-final-data/`.
- English second run: `aqistudy-data-v2/` and `aqistudy-final-data-v2/`.
- Chinese crawl folders must contain `配置文件/`, `数据文件/`, `报告文件/`, `日志文件/`, and `代码文件/`.
- Chinese report filename is `审查报告.md`; its body must be Chinese.
- English report filename is `quality_report.md`; its body must be English.

## Low-Tech Run Contract

The generated crawl folder must include a no-parameter runner:

```text
代码文件/
├── 一键运行.py
└── 运行方式.md
```

The visible command in `运行方式.md` should be:

```bash
python 代码文件/一键运行.py
```

Keep command-line parameters inside the runner script so economic researchers can rerun the same collection without learning crawler options.
