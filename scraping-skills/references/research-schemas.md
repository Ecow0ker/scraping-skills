# Research Schemas

All records must preserve provenance:

```text
source_url
final_url
fetched_at
status_code
content_hash
raw_file_path
extractor_name
extractor_version
```

## Common Datasets

### Price or Product

```text
entity_id
observed_at
商品名称
价格
币种
单位
地区
平台
source_url
```

### Housing

```text
entity_id
observed_at
标题
总价
单价
面积
户型
小区
区县
城市
source_url
```

### Jobs

```text
entity_id
observed_at
职位名称
公司
薪资
城市
经验要求
学历要求
发布日期
source_url
```

### Public Announcements or Procurement

```text
entity_id
发布日期
标题
发布机构
地区
公告类型
正文
source_url
```

### Air Quality

```text
entity_id
observed_at
城市
月份
日期
AQI
质量等级
PM2.5
PM10
SO2
NO2
CO
O3
source_url
```

For Chinese air-quality sites, CSV rows should be city-date observations. Raw HTML, encrypted API responses, and decoded response JSON belong in `data/raw/` or `data/metadata/`, not as the main CSV content.

Use Chinese column names when the user asks in Chinese. Use English snake_case column names when the user asks in English. Keep provenance columns in the same language as the final CSV.

## Field Names

Use Chinese field names for Chinese websites when the output is meant for researchers. Keep technical metadata in English. For Stata `.dta`, create safe ASCII variable names and store Chinese labels in a sidecar JSON when needed.
