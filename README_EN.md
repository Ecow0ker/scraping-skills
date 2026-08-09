# Scraping Skills: Research Data Collection and Structuring Skill

[简体中文](README.md) | [English](README_EN.md)

> **Note:**
> - This project is designed for research data collection and organization. Its goal is not to bypass website restrictions, but to turn public or authorized data sources into reproducible, analysis-ready datasets.
> - For pages that require login, captcha, QR code, MFA, or manual confirmation, the user should complete legitimate verification in a local browser before collection continues.

---

## Community and Feedback

To share your experience, report issues, or suggest improvements, follow the WeChat official account “经实研读” or join QQ group 610645081.

---

## Overview

Scraping Skills is a Codex Skill for collecting and structuring web data for research. It helps researchers convert web pages, APIs, downloads, and authenticated pages into usable research datasets instead of saving only page text, titles, or screenshots.

This project is useful for:

- Collecting city-date historical air quality data.
- Structuring city-date search index data from authenticated Baidu Index pages.
- Collecting housing listings, job postings, product prices, announcements, organization pages, and news indexes.
- Producing observation-level tables such as city-date, organization-date, job-posting, housing-listing, price, and announcement records.
- Exporting CSV, JSONL, Excel, Stata DTA, Parquet, and DuckDB files.
- Generating reusable run scripts and review reports for repeated data collection tasks.

---

## Design Rationale

The core idea behind this Skill is that research data work needs data, not web pages.

Therefore, this project separates web scraping into three connected tasks:

1. **Identify the research observation**

   First decide what one row of the final dataset should represent: city-date, organization-date, job posting, housing listing, price observation, announcement, news item, or search index observation.

2. **Choose the data access path**

   Prefer public downloads, official APIs, or JSON endpoints behind the page. If JavaScript is required, use Scrapling or Playwright. If login, captcha, or manual confirmation is required, open local Chrome and wait for the user to complete verification.

3. **Deliver research data**

   Save raw evidence, metadata, processed data, and a review report. The final CSV should be a structured dataset that researchers can import into Stata, R, Python, or Excel.

The goal is not to scrape as many pages as possible. The goal is to build stable, restrained, and auditable research datasets.

---

## Installation

### Method 1: Ask Codex to Install It (recommended)

Send this prompt directly to Codex:

```text
Please install this Codex skill from the repository:
https://github.com/Ecow0ker/scraping-skills.git

Please copy the complete scraping-skills/ skill folder from the repository into my ~/.codex/skills/ directory, including agents/, references/, and scripts/.
Do not copy only SKILL.md.
If an older version exists, remove ~/.codex/skills/scraping-skills before copying.
```

### Method 2: Install with Git

This method copies the complete Skill folder into the global skills directory currently used by Codex:

```bash
rm -rf /tmp/scraping-skills
mkdir -p ~/.codex/skills
git clone https://github.com/Ecow0ker/scraping-skills.git /tmp/scraping-skills
rm -rf ~/.codex/skills/scraping-skills
cp -R /tmp/scraping-skills/scraping-skills ~/.codex/skills/
```

### Method 3: Manual Local Installation

The Skill folder in this project is:

```text
scraping-skills/
```

Copy it to your Codex skills directory:

```bash
mkdir -p ~/.codex/skills
rm -rf ~/.codex/skills/scraping-skills
cp -R scraping-skills ~/.codex/skills/
```

### Verify Installation

Restart Codex or reload skills, then type:

```text
$scraping-skills
```

If installation succeeds, the Skill should activate.

---

## Usage

### Basic Usage

Call the Skill directly. Chinese prompts default to Chinese folders, Chinese column names, and a Chinese review report. English prompts default to English folders, English column names, and an English quality report.

```text
$scraping-skills Collect this month's air quality data for popular cities from an air quality history website, URL is XXX.
```

```text
$scraping-skills Collect Baidu Index data for every city in Shandong over the past 30 days, URL is XXX.
```

```text
$scraping-skills Collect housing listing data from the first 6 pages for Beijing, URL is XXX.
```

```text
$scraping-skills Collect job postings from this website and export CSV and Stata DTA, URL is XXX.
```

### Pages That Require Login Or Verification

If a page requires login, captcha, QR code, MFA, manual confirmation, or an existing browser session, the Skill opens local Chrome by default and waits for the user to complete verification.

After verification, the user should explicitly tell Codex:

```text
I completed verification. Continue collection.
```

The Skill does not read or save passwords, cookies, local storage, browser cache, or account credentials.

---

## Examples

### Example 1: Historical Air Quality

**Input:**

```text
$scraping-skills Collect this month's air quality data for popular cities from an air quality history website, URL is XXX.
```

**Output direction:**

```text
air-quality-data/
air-quality-final-data/
```

The final dataset includes city, month, date, AQI, quality level, PM2.5, PM10, SO2, NO2, CO, O3, and related provenance fields, with CSV, JSONL, and Stata DTA outputs.

### Example 2: Baidu Index

**Input:**

```text
$scraping-skills Collect Baidu Index data for every city in Shandong over the past 30 days, URL is XXX.
```

**How it works:**

If Baidu Index requires login, the Skill opens local Chrome, waits for the user to complete login or verification, and then structures city-date search index data.

### Example 3: Housing Or Job Listings

**Input:**

```text
$scraping-skills Collect job postings from the first 5 pages of this website, URL is XXX.
```

**Output direction:**

The final dataset should include job title, company, city, salary, experience requirement, education requirement, posting date, source URL, and provenance fields, instead of only saving listing-page text.

---

## Files

```text
scraping-skills/
├── SKILL.md
├── agents/
│   └── openai.yaml
├── references/
│   └── ...
└── scripts/
    └── ...
```

File notes:

- `SKILL.md`: Main Skill entry point, trigger contexts, default workflow, and output rules.
- `agents/`: Codex interface metadata and default prompt configuration.
- `references/`: Rules for source classification, engine selection, login and verification workflows, data schemas, quality checks, and compliance boundaries.
- `scripts/`: Reusable scripts for extraction, raw evidence archiving, listing-detail crawling, and quality reporting.

Note: `scraping-skills/references/` contains internal Skill rule files. It is not an output data folder.

---

## Output Convention

By default, outputs are written directly under the current workspace root. The Skill does not add an extra `test-runs/<scenario>/` wrapper.

English tasks usually create:

```text
data-crawl-folder/
├── config/
├── data/
│   ├── raw/
│   ├── processed/
│   └── metadata/
├── reports/
├── logs/
└── code/
final-data-folder/
└── CSV / JSONL / DTA / XLSX / Parquet / DuckDB
```

For historical air quality data, folder names usually are:

```text
air-quality-data/
air-quality-final-data/
```

The first run has no version suffix. The second run uses `-v2`, and the third run uses `-v3`.

---

## Core Principles

### CSV Is Research Data, Not Page Text

The final CSV should contain meaningful research observations. For air quality tasks, one row should be a city-date observation. For housing tasks, one row should be a listing. For job tasks, one row should be a job posting.

### Preserve Raw Evidence

Each record should preserve source URL, final URL, fetch time, status code, content hash, raw file path, and extractor version when possible, so the dataset can be audited later.

### Do Not Bypass Access Controls

The Skill does not automatically bypass login, paywalls, captchas, identity verification, or access controls. When human verification is required, the user completes it in a local browser.

### Use Conservative Crawl Pacing

Multi-page collection defaults to one page every 10 seconds with conservative concurrency.

## License

This project is licensed under the [Apache License 2.0](LICENSE).
