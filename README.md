# Scraping Skills：研究类数据抓取与整理 Skills

[简体中文](README.md) | [English](README_EN.md)

> **声明：**
> - 本项目面向研究类数据整理场景，重点不是绕过网站限制，而是把公开或授权访问的数据源整理成可复核、可分析、可导出的研究数据集。
> - 需要登录、验证码、二维码、MFA 或人工确认的网页，应由用户在本机浏览器中完成合法验证后再继续。

---

## 交流与反馈

如需交流使用体验、反馈问题或提出改进建议，欢迎关注微信公众号“经实研读”，或加入 QQ 群：610645081。

---

## 项目简介

Scraping Skills 是一个用于研究类网页数据抓取和整理的 Codex Skill。它可以帮助研究人员把网页、接口、下载文件或登录后可见页面整理成真正可用的研究数据，而不是只保存网页正文、标题或截图。

本项目适用于：

- 抓取城市-日期空气质量历史数据。
- 整理百度指数等登录后页面中的城市-日期搜索指数。
- 抓取房产挂牌、招聘岗位、商品价格、公告、机构页面和新闻索引。
- 将网页内容整理成城市-日期、机构-日期、岗位、房产、价格、公告等 observation-level 表格。
- 输出 CSV、JSONL、Excel、Stata DTA、Parquet、DuckDB 等研究常用格式。
- 为重复性数据收集任务生成可复用的运行脚本和审查报告。

---

## 设计思路

这个 Skill 的核心判断是：研究类数据整理需要的是数据，而不是网页。

因此，本项目把“爬虫”拆成三层：

1. **研究对象识别**

   先判断最终数据的一行应该是什么：城市-日期、机构-日期、岗位、房产挂牌、价格观测、公告、新闻条目，还是搜索指数观测。

2. **数据源路径选择**

   优先使用公开下载、官方 API 或网页背后的 JSON 数据；如果页面需要 JavaScript，再考虑 Scrapling 或 Playwright；如果需要登录、验证码或人工确认，则默认使用本机 Chrome 等待用户完成验证。

3. **研究数据交付**

   保存原始证据、元数据和处理后数据，并生成审查报告。最终 CSV 不是网页 dump，而是研究者可以直接导入 Stata、R、Python 或 Excel 的结构化数据。

最终目标不是“尽可能多地抓网页”，而是稳定、克制、可复核地构造研究数据。

---

## 安装

### 方法一：让 Codex 帮你安装（推荐）

直接把下面这段提示词发给 Codex：

```text
请从这个仓库安装 Codex skill：
https://github.com/Ecow0ker/scraping-skills.git

请把仓库中的 scraping-skills/ 完整技能文件夹安装到我的 ~/.codex/skills/ 目录中，包括 agents/、references/ 和 scripts/。
不要只复制 SKILL.md。
如果已存在旧版本，请先删除 ~/.codex/skills/scraping-skills 再复制。
```

### 方法二：通过 Git 克隆安装

该方法会把完整 Skill 文件夹复制到 Codex 当前使用的全局 skills 目录：

```bash
rm -rf /tmp/scraping-skills
mkdir -p ~/.codex/skills
git clone https://github.com/Ecow0ker/scraping-skills.git /tmp/scraping-skills
rm -rf ~/.codex/skills/scraping-skills
cp -R /tmp/scraping-skills/scraping-skills ~/.codex/skills/
```

### 方法三：本地手动安装

当前 Skill 已生成在本项目目录中：

```text
scraping-skills/
```

可以复制到 Codex skills 目录：

```bash
mkdir -p ~/.codex/skills
rm -rf ~/.codex/skills/scraping-skills
cp -R scraping-skills ~/.codex/skills/
```

### 验证安装

重启 Codex 或重新加载 skills 后，在对话中输入：

```text
$scraping-skills
```

如果安装成功，该 Skill 将被激活。

---

## 使用

### 基础用法

直接调用 Skill 即可。中文提问会默认生成中文目录、中文字段名和中文审查报告；英文提问会默认生成英文目录、英文字段名和英文质量报告。

```text
$scraping-skills 请爬取某空气质量历史数据网站中热门城市这个月的空气质量，网址为XXX。
```

```text
$scraping-skills 请获取山东每个城市近30天的百度搜索指数，网址为XXX。
```

```text
$scraping-skills 请抓取北京前6页的房产挂牌数据，网址为XXX。
```

```text
$scraping-skills Collect job postings from this website and export CSV and Stata DTA, URL is XXX.
```

### 需要登录或验证的网页

如果页面需要登录、验证码、二维码、MFA、人工确认或已有浏览器会话，Skill 默认使用本机 Chrome 打开页面，并等待用户完成验证。

用户完成验证后，需要明确告诉 Codex：

```text
已完成验证，继续抓取。
```

Skill 不会读取或保存密码、cookie、local storage、浏览器缓存或账号凭据。

---

## 使用场景示例

### 场景 1：城市空气质量

**输入：**

```text
$scraping-skills 请爬取某空气质量历史数据网站中热门城市这个月的空气质量，网址为XXX。
```

**输出方向：**

```text
空气质量数据抓取/
空气质量最终数据/
```

最终数据包含城市、月份、日期、AQI、质量等级、PM2.5、PM10、SO2、NO2、CO、O3 等字段，并输出 CSV、JSONL 和 Stata DTA。

### 场景 2：百度指数

**输入：**

```text
$scraping-skills 请获取山东每个城市近30天的百度搜索指数，网址为XXX。
```

**处理方式：**

如果百度指数需要登录，Skill 会打开本机 Chrome，等待用户完成登录或验证，然后继续整理城市-日期层面的搜索指数数据。

### 场景 3：房产或招聘列表

**输入：**

```text
$scraping-skills 请抓取这个网站前5页的招聘岗位数据，网址为XXX。
```

**输出方向：**

最终数据应包含岗位名称、公司、城市、薪资、经验要求、学历要求、发布日期、来源网址等字段，而不是只保存列表页正文。

---

## 文件说明

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

说明：

- `SKILL.md`：Skill 主入口，定义触发场景、默认工作流和输出约定。
- `agents/`：Codex 界面显示和默认提示词配置。
- `references/`：网页类型判断、采集方式选择、登录验证、人机交互、数据结构、质量检查和合规边界等规则。
- `scripts/`：可复用的数据抽取、原始证据保存、列表详情页抓取和质量报告脚本。

注意：`scraping-skills/references/` 是 Skill 内部规则文档目录，不是输出数据目录。

---

## 输出约定

默认直接在当前工作根目录生成结果，不额外包一层 `test-runs/<场景名>/`。

中文任务通常生成：

```text
数据抓取目录/
├── 配置文件/
├── 数据文件/
│   ├── 原始文件/
│   ├── 处理后数据/
│   └── 元数据/
├── 报告文件/
├── 日志文件/
└── 代码文件/
最终数据目录/
└── CSV / JSONL / DTA / XLSX / Parquet / DuckDB
```

对于空气质量历史数据，目录名通常为：

```text
空气质量数据抓取/
空气质量最终数据/
```

第一次运行没有版本后缀；第二次运行使用 `V2`，第三次使用 `V3`。

---

## 关键原则

### CSV 是研究数据，不是网页正文

最终 CSV 应该包含有意义的研究观测行。例如空气质量任务中，一行应是一个城市-日期观测；房产任务中，一行应是一条房产挂牌；招聘任务中，一行应是一条岗位。

### 保留原始证据

每条记录应尽量保留来源网址、最终网址、抓取时间、状态码、内容哈希、原始文件路径和抽取器版本，方便之后复核。

### 不绕过访问控制

Skill 不自动绕过登录、付费墙、验证码、身份验证或访问控制。需要人工验证时，由用户在本机浏览器中完成。

### 控制抓取节奏

多页抓取默认 10 秒一页，保守并发，避免给网站造成不必要压力。

## 许可证

本项目采用 [Apache License 2.0](LICENSE)。
