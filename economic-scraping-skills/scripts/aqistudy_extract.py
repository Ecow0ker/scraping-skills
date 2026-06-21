#!/usr/bin/env python3
"""Collect aqistudy air-quality history as an observation-level dataset."""

from __future__ import annotations

import argparse
import base64
import hashlib
import html
import json
import re
import shutil
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from save_raw_response import (
    EXTRACTOR_VERSION,
    FetchResult,
    ensure_project_dirs,
    export_records,
    fetch_url,
    parse_formats,
    save_raw_response,
    utc_now,
)
from quality_report import report_file_name, write_report
from single_page_extract import decode_body


BASE_URL = "https://www.aqistudy.cn/historydata/"
INDEX_URL = urllib.parse.urljoin(BASE_URL, "index.php")
API_URL = urllib.parse.urljoin(BASE_URL, "api/historyapi.php")
API_METHOD = "GETDAYDATA"

APP_ID = "3c9208efcfb2f5b843eec8d96de6d48a"
CLIENT_TYPE = "WEB"

AES_RESPONSE_KEY = "a0QHmC1Ova5958nC"
AES_RESPONSE_IV = "bMu71lHRX6bRmPxU"
AES_REQUEST_KEY = "dLRSzDrm8xkryEyL"
AES_REQUEST_IV = "fex6AA4zRfVrSPmr"
DES_KEY = "hEaIOlrX7tlhAOkz"
DES_IV = "xMBwDXG1HOubUV04"

DEFAULT_DATA_COLUMNS = [
    "entity_id",
    "城市",
    "月份",
    "日期",
    "AQI",
    "质量等级",
    "PM2.5",
    "PM10",
    "SO2",
    "NO2",
    "CO",
    "O3",
    "排名",
    "数据状态",
]

EN_DEFAULT_DATA_COLUMNS = [
    "entity_id",
    "city",
    "month",
    "date",
    "aqi",
    "quality_level",
    "pm2_5",
    "pm10",
    "so2",
    "no2",
    "co",
    "o3",
    "rank",
    "data_status",
]

PROVENANCE_COLUMNS = [
    "source_url",
    "final_url",
    "page_url",
    "fetched_at",
    "status_code",
    "content_hash",
    "raw_file_path",
    "page_raw_file_path",
    "metadata_file_path",
    "extractor_name",
    "extractor_version",
    "api_method",
]

CODE_BUNDLE_SCRIPTS = [
    "aqistudy_extract.py",
    "save_raw_response.py",
    "single_page_extract.py",
    "quality_report.py",
]

ZH_COLUMN_NAMES = {
    "entity_id": "实体ID",
    "source_url": "来源网址",
    "final_url": "最终网址",
    "page_url": "页面网址",
    "fetched_at": "抓取时间",
    "status_code": "状态码",
    "content_hash": "内容哈希",
    "raw_file_path": "原始文件路径",
    "page_raw_file_path": "页面原始文件路径",
    "metadata_file_path": "元数据文件路径",
    "extractor_name": "抽取器名称",
    "extractor_version": "抽取器版本",
    "api_method": "接口方法",
    "extraction_errors": "抽取错误",
}

EN_COLUMN_NAMES = {
    "城市": "city",
    "月份": "month",
    "日期": "date",
    "AQI": "aqi",
    "质量等级": "quality_level",
    "PM2.5": "pm2_5",
    "PM10": "pm10",
    "SO2": "so2",
    "NO2": "no2",
    "CO": "co",
    "O3": "o3",
    "排名": "rank",
    "数据状态": "data_status",
    "抽取错误": "extraction_errors",
}

COLUMN_ALIASES = {
    "entity_id": "entity_id",
    "实体ID": "entity_id",
    "城市": "城市",
    "city": "城市",
    "月份": "月份",
    "month": "月份",
    "日期": "日期",
    "date": "日期",
    "AQI": "AQI",
    "aqi": "AQI",
    "质量等级": "质量等级",
    "quality": "质量等级",
    "quality_level": "质量等级",
    "PM2.5": "PM2.5",
    "PM2_5": "PM2.5",
    "pm2_5": "PM2.5",
    "PM10": "PM10",
    "pm10": "PM10",
    "SO2": "SO2",
    "so2": "SO2",
    "NO2": "NO2",
    "no2": "NO2",
    "CO": "CO",
    "co": "CO",
    "O3": "O3",
    "o3": "O3",
    "排名": "排名",
    "rank": "排名",
    "数据状态": "数据状态",
    "data_status": "数据状态",
}


def require_crypto() -> tuple[Any, Any, Any, Any]:
    try:
        from cryptography.hazmat.decrepit.ciphers.algorithms import TripleDES
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        from cryptography.hazmat.primitives.padding import PKCS7
    except Exception as exc:
        raise RuntimeError(
            "aqistudy_extract.py needs the cryptography package. "
            "Run setup_environment.py --install --extras pandas,openpyxl,cryptography"
        ) from exc
    return Cipher, algorithms, modes, (PKCS7, TripleDES)


Cipher, algorithms, modes, crypto_extra = require_crypto()
PKCS7, TripleDES = crypto_extra


def pkcs7_pad(data: bytes, block_bits: int) -> bytes:
    padder = PKCS7(block_bits).padder()
    return padder.update(data) + padder.finalize()


def pkcs7_unpad(data: bytes, block_bits: int) -> bytes:
    unpadder = PKCS7(block_bits).unpadder()
    return unpadder.update(data) + unpadder.finalize()


def md5_hex(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def aes_key_iv(key: str, iv: str) -> tuple[bytes, bytes]:
    secret_key = md5_hex(key)[16:32].encode("utf-8")
    secret_iv = md5_hex(iv)[0:16].encode("utf-8")
    return secret_key, secret_iv


def des_key_iv(key: str, iv: str) -> tuple[bytes, bytes]:
    secret_key = md5_hex(key)[0:16].encode("utf-8")[:8] * 3
    secret_iv = md5_hex(iv)[24:32].encode("utf-8")
    return secret_key, secret_iv


def aes_encrypt(text: str, key: str, iv: str) -> str:
    secret_key, secret_iv = aes_key_iv(key, iv)
    padded = pkcs7_pad(text.encode("utf-8"), 128)
    encryptor = Cipher(algorithms.AES(secret_key), modes.CBC(secret_iv)).encryptor()
    encrypted = encryptor.update(padded) + encryptor.finalize()
    return base64.b64encode(encrypted).decode("ascii")


def aes_decrypt(text: str, key: str, iv: str) -> str:
    secret_key, secret_iv = aes_key_iv(key, iv)
    encrypted = base64.b64decode(text)
    decryptor = Cipher(algorithms.AES(secret_key), modes.CBC(secret_iv)).decryptor()
    padded = decryptor.update(encrypted) + decryptor.finalize()
    return pkcs7_unpad(padded, 128).decode("utf-8")


def des_decrypt(text: str, key: str, iv: str) -> str:
    secret_key, secret_iv = des_key_iv(key, iv)
    encrypted = base64.b64decode(text)
    decryptor = Cipher(TripleDES(secret_key), modes.CBC(secret_iv)).decryptor()
    padded = decryptor.update(encrypted) + decryptor.finalize()
    return pkcs7_unpad(padded, 64).decode("utf-8")


def compact_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def make_api_payload(method: str, request_object: dict[str, Any]) -> str:
    timestamp = int(time.time() * 1000)
    sorted_object = {key: request_object[key] for key in sorted(request_object)}
    secret = md5_hex(APP_ID + method + str(timestamp) + CLIENT_TYPE + compact_json(sorted_object))
    payload = {
        "appId": APP_ID,
        "method": method,
        "timestamp": timestamp,
        "clienttype": CLIENT_TYPE,
        "object": request_object,
        "secret": secret,
    }
    encoded = base64.b64encode(compact_json(payload).encode("utf-8")).decode("ascii")
    return aes_encrypt(encoded, AES_REQUEST_KEY, AES_REQUEST_IV)


def decode_api_response(response_text: str) -> dict[str, Any]:
    decoded = base64.b64decode(response_text).decode("utf-8")
    decoded = des_decrypt(decoded, DES_KEY, DES_IV)
    decoded = aes_decrypt(decoded, AES_RESPONSE_KEY, AES_RESPONSE_IV)
    decoded = base64.b64decode(decoded).decode("utf-8")
    return json.loads(decoded)


def day_url(city: str, month: str) -> str:
    query = urllib.parse.urlencode({"city": city, "month": month})
    return urllib.parse.urljoin(BASE_URL, f"daydata.php?{query}")


def month_url(city: str) -> str:
    query = urllib.parse.urlencode({"city": city})
    return urllib.parse.urljoin(BASE_URL, f"monthdata.php?{query}")


def fetch_page(
    url: str,
    project_dir: str | Path,
    mode: str,
    timeout: int,
    language: str,
    referer: str | None = None,
) -> tuple[str, dict[str, Any]]:
    headers = {"Referer": referer} if referer else None
    result = fetch_url(url, timeout=timeout, mode=mode, headers=headers)
    metadata = save_raw_response(result, project_dir, language=language)
    return decode_body(result.body, result.headers), metadata


def fetch_api_day(
    city: str,
    month: str,
    project_dir: str | Path,
    timeout: int,
    referer: str,
    language: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    request_object = {"city": city, "month": month}
    payload = make_api_payload(API_METHOD, request_object)
    body = urllib.parse.urlencode({"hA4Nse2cT": payload}).encode("utf-8")
    request = urllib.request.Request(
        API_URL,
        data=body,
        headers={
            "User-Agent": "Mozilla/5.0 research-collector/0.1",
            "Referer": referer,
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest",
        },
    )
    fetched_at = utc_now()
    with urllib.request.urlopen(request, timeout=timeout) as response:
        response_body = response.read()
        result = FetchResult(
            source_url=API_URL,
            final_url=response.geturl(),
            status_code=getattr(response, "status", 200),
            headers={key: value for key, value in response.headers.items()},
            body=response_body,
            fetched_at=fetched_at,
            fetcher_name="aqistudy.historyapi",
        )

    metadata = save_raw_response(result, project_dir, language=language)
    metadata.update({"api_method": API_METHOD, "api_object": request_object, "page_url": referer})
    Path(metadata["metadata_file_path"]).write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")

    decoded = decode_api_response(response_body.decode("utf-8"))
    paths = ensure_project_dirs(Path(project_dir), language=language)
    decoded_path = paths["metadata"] / f"aqistudy_{city}_{month}_decoded_response.json"
    decoded_path.write_text(json.dumps(decoded, ensure_ascii=False, indent=2), encoding="utf-8")
    metadata["decoded_response_file_path"] = str(decoded_path)
    Path(metadata["metadata_file_path"]).write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    return decoded, metadata


def extract_hot_cities(index_html: str) -> list[str]:
    cities: list[str] = []
    try:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(index_html, "html.parser")
        hot = soup.find("div", class_="hot")
        scope = hot if hot else soup
        for link in scope.find_all("a", href=True):
            href = link.get("href", "")
            if "monthdata.php?city=" not in href:
                continue
            city = link.get_text(strip=True) or urllib.parse.parse_qs(urllib.parse.urlsplit(href).query).get("city", [""])[0]
            city = city.strip()
            if city and city not in cities:
                cities.append(city)
    except Exception:
        block_match = re.search(r'<div[^>]+class=["\'][^"\']*hot[^"\']*["\'][^>]*>(.*?)</div>', index_html, flags=re.I | re.S)
        scope = block_match.group(1) if block_match else index_html
        for href_city, text_city in re.findall(r'<a[^>]+href=["\'][^"\']*monthdata\.php\?city=([^"\']+)["\'][^>]*>(.*?)</a>', scope, flags=re.I | re.S):
            city = re.sub(r"<[^>]+>", "", text_city).strip() or urllib.parse.unquote(href_city)
            city = html.unescape(city)
            if city and city not in cities:
                cities.append(city)
    return cities


def extract_months(page_html: str, city: str) -> list[str]:
    months: list[str] = []
    for month in re.findall(r"daydata\.php\?city=[^\"'&<>]+&month=(\d{6})", page_html):
        if month not in months:
            months.append(month)
    if not months:
        escaped_city = re.escape(urllib.parse.quote(city))
        pattern = rf"daydata\.php\?city={escaped_city}&month=(\d{{6}})"
        for month in re.findall(pattern, page_html):
            if month not in months:
                months.append(month)
    return sorted(months)


def choose_month(available_months: list[str], requested: str) -> str:
    requested = requested.strip().lower()
    if requested != "latest":
        if not re.fullmatch(r"\d{6}", requested):
            raise ValueError("--month must be latest or YYYYMM")
        return requested
    if not available_months:
        return time.strftime("%Y%m")
    return max(available_months)


def parse_list(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [item.strip() for item in re.split(r"[,，]", raw) if item.strip()]


def normalize_language(raw: str) -> str:
    value = raw.strip().lower()
    if value in {"zh", "cn", "chinese", "中文"}:
        return "zh"
    if value in {"en", "english", "英文"}:
        return "en"
    return "zh"


def normalize_version(raw: str) -> str:
    cleaned = raw.strip() or "V2"
    if cleaned.lower() == "auto":
        return "auto"
    if cleaned in {"1", "V1", "v1", "无", "none", "None"}:
        return ""
    if re.fullmatch(r"\d+", cleaned):
        return f"V{cleaned}"
    if re.fullmatch(r"v\d+", cleaned, flags=re.I):
        return "V" + cleaned[1:]
    return cleaned


def run_index_to_version(index: int) -> str:
    return "" if index <= 1 else f"V{index}"


def version_to_slug(version: str) -> str:
    return version.lower() if version else ""


def crawl_base_name(language: str) -> str:
    return "aqistudy数据抓取" if language == "zh" else "aqistudy-data"


def final_base_name(language: str) -> str:
    return "aqistudy最终数据" if language == "zh" else "aqistudy-final-data"


def name_with_version(base_name: str, version: str, language: str) -> str:
    if not version:
        return base_name
    if language == "zh":
        return f"{base_name}{version}"
    return f"{base_name}-{version_to_slug(version)}"


def parse_run_index(name: str, language: str, kind: str) -> int | None:
    base = crawl_base_name(language) if kind == "crawl" else final_base_name(language)
    if language == "zh":
        pattern = rf"^{re.escape(base)}(?:V(\d+))?$"
    else:
        pattern = rf"^{re.escape(base)}(?:-v(\d+))?$"
    match = re.match(pattern, name, flags=re.I)
    if not match:
        return None
    if not match.group(1):
        return 1
    return int(match.group(1))


def detect_next_version(parent_dir: Path, language: str) -> str:
    max_index = 0
    if parent_dir.exists():
        for child in parent_dir.iterdir():
            if not child.is_dir():
                continue
            for kind in ("crawl", "final"):
                index = parse_run_index(child.name, language, kind)
                if index:
                    max_index = max(max_index, index)
    return run_index_to_version(max_index + 1)


def output_parent_from_args(project_dir: str | None, output_parent: str | None) -> Path:
    if output_parent:
        return Path(output_parent)
    if project_dir:
        path = Path(project_dir)
        return path.parent if path.parent != Path("") else Path(".")
    return Path(".")


def default_project_dir(parent_dir: Path, language: str, version: str) -> Path:
    return parent_dir / name_with_version(crawl_base_name(language), version, language)


def default_final_dir(parent_dir: Path, language: str, version: str) -> Path:
    return parent_dir / name_with_version(final_base_name(language), version, language)


def resolve_project_dirs(
    project_dir: str | None,
    output_parent: str | None,
    language: str,
    version: str,
) -> tuple[Path, Path, str]:
    parent_dir = output_parent_from_args(project_dir, output_parent)
    resolved_version = detect_next_version(parent_dir, language) if version == "auto" else version
    return (
        default_project_dir(parent_dir, language, resolved_version),
        default_final_dir(parent_dir, language, resolved_version),
        resolved_version,
    )


def default_stem(language: str, version: str) -> str:
    if language == "zh":
        return f"aqistudy空气质量数据{version}" if version else "aqistudy空气质量数据"
    slug = version_to_slug(version)
    return f"aqistudy_air_quality_{slug}" if slug else "aqistudy_air_quality"


def code_file_names(language: str) -> tuple[str, str]:
    if language == "zh":
        return "一键运行.py", "运行方式.md"
    return "run.py", "how_to_run.md"


def write_code_bundle(project_dir: Path, language: str) -> dict[str, str]:
    paths = ensure_project_dirs(project_dir, language=language)
    code_dir = paths["code"]
    runner_name, instructions_name = code_file_names(language)

    for script_name in CODE_BUNDLE_SCRIPTS:
        source = SCRIPT_DIR / script_name
        target = code_dir / script_name
        if source.exists() and source.resolve() != target.resolve():
            shutil.copy2(source, target)

    output_parent = project_dir.parent
    runner_path = code_dir / runner_name
    runner_text = f"""#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


SCRIPT = Path(__file__).resolve().parent / "aqistudy_extract.py"
OUTPUT_PARENT = Path(r"{output_parent}")
LANGUAGE = "{language}"


def main() -> int:
    command = [
        sys.executable,
        str(SCRIPT),
        "--output-parent",
        str(OUTPUT_PARENT),
        "--language",
        LANGUAGE,
    ]
    subprocess.run(command, check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
"""
    runner_path.write_text(runner_text, encoding="utf-8")
    try:
        runner_path.chmod(0o755)
    except OSError:
        pass

    if language == "zh":
        instructions = f"""# 运行方式

第一次使用只需安装一次：

```bash
python -m pip install "scrapling[all]" pandas openpyxl cryptography
```

以后抓取同类数据，在 `{project_dir.name}` 文件夹里运行：

```bash
python 代码文件/一键运行.py
```

不用加参数。脚本会自动抓取 aqistudy 热门城市当月空气质量，并把 CSV、JSONL 和 Stata DTA 放到同级目录的新版本文件夹中。
"""
    else:
        instructions = f"""# How To Run

Install dependencies once:

```bash
python -m pip install "scrapling[all]" pandas openpyxl cryptography
```

For the same collection, run this inside `{project_dir.name}`:

```bash
python code/run.py
```

No parameters are needed. The script collects aqistudy hot-city air quality for the current month and writes CSV, JSONL, and Stata DTA files beside this folder.
"""
    instructions_path = code_dir / instructions_name
    instructions_path.write_text(instructions, encoding="utf-8")
    return {"code_dir": str(code_dir), "runner": str(runner_path), "instructions": str(instructions_path)}


def normalize_requested_columns(raw_columns: list[str]) -> list[str]:
    normalized: list[str] = []
    for column in raw_columns:
        key = COLUMN_ALIASES.get(column, COLUMN_ALIASES.get(column.strip(), column))
        if key not in normalized:
            normalized.append(key)
    return normalized


def localize_record(record: dict[str, Any], language: str) -> dict[str, Any]:
    if language == "en":
        mapping = EN_COLUMN_NAMES
    else:
        mapping = ZH_COLUMN_NAMES

    localized: dict[str, Any] = {}
    for key, value in record.items():
        localized_key = mapping.get(key, key)
        localized[localized_key] = value
    return localized


def core_metadata(api_metadata: dict[str, Any], page_metadata: dict[str, Any], page_url_value: str) -> dict[str, Any]:
    return {
        "source_url": api_metadata["source_url"],
        "final_url": api_metadata["final_url"],
        "page_url": page_url_value,
        "fetched_at": api_metadata["fetched_at"],
        "status_code": api_metadata["status_code"],
        "content_hash": api_metadata["content_hash"],
        "raw_file_path": api_metadata["raw_file_path"],
        "page_raw_file_path": page_metadata["raw_file_path"],
        "metadata_file_path": api_metadata["metadata_file_path"],
        "extractor_name": "aqistudy_historyapi+scrapling",
        "extractor_version": EXTRACTOR_VERSION,
        "api_method": API_METHOD,
    }


def records_from_response(
    decoded: dict[str, Any],
    city: str,
    month: str,
    api_metadata: dict[str, Any],
    page_metadata: dict[str, Any],
    page_url_value: str,
) -> list[dict[str, Any]]:
    metadata = core_metadata(api_metadata, page_metadata, page_url_value)
    outer_success = decoded.get("success") is True
    result = decoded.get("result") if isinstance(decoded.get("result"), dict) else {}
    data = result.get("data") if isinstance(result.get("data"), dict) else {}
    items = data.get("items") if isinstance(data.get("items"), list) else []
    if not outer_success or not items:
        return [
            {
                "entity_id": f"aqistudy:{city}:{month}:no_data",
                "城市": city,
                "月份": month,
                "日期": "",
                "AQI": "",
                "质量等级": "",
                "PM2.5": "",
                "PM10": "",
                "SO2": "",
                "NO2": "",
                "CO": "",
                "O3": "",
                "排名": "",
                "数据状态": "no_items",
                "extraction_errors": decoded.get("errmsg", "API returned no day-level items"),
                **metadata,
            }
        ]

    records: list[dict[str, Any]] = []
    for item in items:
        date_value = item.get("time_point", "")
        records.append(
            {
                "entity_id": f"aqistudy:{city}:{date_value}",
                "城市": city,
                "月份": month,
                "日期": date_value,
                "AQI": item.get("aqi", ""),
                "质量等级": item.get("quality", ""),
                "PM2.5": item.get("pm2_5", ""),
                "PM10": item.get("pm10", ""),
                "SO2": item.get("so2", ""),
                "NO2": item.get("no2", ""),
                "CO": item.get("co", ""),
                "O3": item.get("o3", ""),
                "排名": item.get("rank", ""),
                "数据状态": "ok",
                **metadata,
            }
        )
    return records


def project_columns(records: list[dict[str, Any]], requested_columns: list[str], language: str) -> list[dict[str, Any]]:
    normalized_requested = normalize_requested_columns(requested_columns)
    base_columns = normalized_requested if normalized_requested else DEFAULT_DATA_COLUMNS
    ordered_columns: list[str] = []
    for column in [*base_columns, *PROVENANCE_COLUMNS, "extraction_errors"]:
        if column not in ordered_columns:
            ordered_columns.append(column)

    projected: list[dict[str, Any]] = []
    for record in records:
        new_record: dict[str, Any] = {}
        for column in ordered_columns:
            if column in record:
                new_record[column] = record[column]
            elif column in base_columns:
                new_record[column] = ""
        if not normalized_requested:
            for key, value in record.items():
                if key not in new_record:
                    new_record[key] = value
        projected.append(localize_record(new_record, language))
    return projected


def collect(args: argparse.Namespace) -> dict[str, Any]:
    language = normalize_language(args.language)
    version = normalize_version(args.version)
    project_dir, final_dir, version = resolve_project_dirs(args.project_dir, args.output_parent, language, version)
    stem = args.stem or default_stem(language, version)
    code_bundle = write_code_bundle(project_dir, language)
    index_html, index_metadata = fetch_page(args.index_url, project_dir, args.mode, args.timeout, language)
    cities = parse_list(args.cities) or extract_hot_cities(index_html)
    if args.max_cities:
        cities = cities[: args.max_cities]
    if not cities:
        raise RuntimeError("No cities found. Provide --cities, for example --cities 北京,上海,广州")

    all_records: list[dict[str, Any]] = []
    selected: list[dict[str, str]] = []
    for index, city in enumerate(cities):
        if index and args.download_delay > 0:
            time.sleep(args.download_delay)
        city_month_url = month_url(city)
        month_html, month_metadata = fetch_page(city_month_url, project_dir, args.mode, args.timeout, language, referer=args.index_url)
        months = extract_months(month_html, city)
        month = choose_month(months, args.month)
        city_day_url = day_url(city, month)
        day_html, day_metadata = fetch_page(city_day_url, project_dir, args.mode, args.timeout, language, referer=city_month_url)
        if len(day_html) < 1000:
            day_metadata = month_metadata
        decoded, api_metadata = fetch_api_day(city, month, project_dir, args.timeout, city_day_url, language)
        city_records = records_from_response(decoded, city, month, api_metadata, day_metadata, city_day_url)
        all_records.extend(city_records)
        selected.append({"城市": city, "月份": month, "records": str(len(city_records))})

    requested_columns = parse_list(args.columns)
    all_records = project_columns(all_records, requested_columns, language)
    outputs = export_records(
        all_records,
        project_dir,
        stem,
        parse_formats(args.formats),
        language=language,
        final_dir_name=str(final_dir),
    )
    report_source = Path(outputs.get("final_csv") or outputs.get("csv") or outputs.get("final_jsonl") or outputs.get("jsonl") or stem)
    report_path = ensure_project_dirs(project_dir, language=language)["reports"] / report_file_name(language)
    write_report(all_records, report_path, report_source, language=language)
    return {
        "records": len(all_records),
        "language": language,
        "version": version or "V1",
        "project_dir": str(project_dir),
        "final_data_dir": str(final_dir),
        "review_report": str(report_path),
        "code_bundle": code_bundle,
        "cities": selected,
        "index_raw_file_path": index_metadata["raw_file_path"],
        "outputs": outputs,
        "sample": all_records[:3],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect aqistudy city-day air-quality data into CSV/JSONL/etc.")
    parser.add_argument("--project-dir", default=None)
    parser.add_argument("--output-parent", default=None, help="Parent folder for sibling crawl/final-data directories")
    parser.add_argument("--index-url", default=INDEX_URL)
    parser.add_argument("--cities", help="Comma-separated city names. If omitted, use hot cities from the index page.")
    parser.add_argument("--max-cities", type=int, help="Limit the number of inferred cities.")
    parser.add_argument("--month", default="latest", help="latest or YYYYMM")
    parser.add_argument("--columns", help="Comma-separated data columns to keep before provenance columns.")
    parser.add_argument("--language", choices=["zh", "en"], default="zh", help="Output language for folders and column names")
    parser.add_argument("--version", default="auto", help="auto, V2, V3, or 1. First auto run has no version suffix.")
    parser.add_argument("--mode", choices=["auto", "static"], default="auto")
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--download-delay", type=float, default=10.0)
    parser.add_argument("--formats", default="csv,jsonl,dta")
    parser.add_argument("--stem", default=None)
    args = parser.parse_args()

    result = collect(args)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
