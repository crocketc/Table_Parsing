## Context

本模块是表格数据处理管线的第一步——解析层。上游是各种来源的 CSV/XLS/XLSX 文件（ERP 导出、手工录入、历史系统迁移等），下游是数据清洗、分类、入库和向量化模块。当前项目为零起点，无现有代码约束。

核心挑战：
- **编码混乱**：历史系统导出的 CSV 大量使用 GBK/GB2312，纯 UTF-8 假设会导致乱码
- **格式异构**：XLS（OLE2 二进制）和 XLSX（OOXML ZIP）结构完全不同，需不同的解析库
- **信息无损**：合并区域、公式、隐藏行列等结构信息在下游清洗时有重要价值，不能丢弃
- **大文件压力**：部分 CSV 超过 100MB，全量加载会 OOM

## Goals / Non-Goals

**Goals:**
- 对 CSV/XLS/XLSX 三种格式提供统一的解析接口，输出纯 Python dataclass IR
- IR 不依赖 pandas，下游可以自由选择处理框架
- 保留原始文件中的所有结构信息（合并、公式、隐藏、样式）
- 对编码问题和文件损坏具备鲁棒性
- 通过配置开关控制可选项（媒体提取、分块等）

**Non-Goals:**
- 不支持 Google Sheets、Numbers 等其他表格格式
- 不实现公式计算引擎（仅提取公式原文和缓存值）
- 不做数据清洗或类型推断（交给下游模块）
- 不提供 CLI 或 REST 接口（本模块是纯库）
- P2 多媒体 AI 理解能力首期实现基础框架，模型 API 可配置

## Decisions

### D1: IR 用 dataclass 而非 dict 或 pydantic

**选择**: `@dataclass` + `field(default=...)`

**替代方案**:
- dict: 灵活但无类型约束，IDE 支持差
- pydantic: 验证强但引入重依赖，且 IR 是内部结构不需要序列化

**理由**: dataclass 零依赖、类型明确、可变（适合逐字段填充）、支持 frozen 模式。`frozen=True` 在调试时可防误改，但填充阶段需要可变，故默认不 frozen。

### D2: CSV 解析底层使用 pandas 引擎

**选择**: `pandas.read_csv()` 作为 CSV 底层解析器

**替代方案**:
- stdlib csv 模块: 对编码和多字节分隔符支持弱
- clevercsv: 自动检测更强但额外依赖且社区较小

**理由**: pandas 的 CSV 解析久经考验，内建 chunksize 支持大文件分块，编码探测配合 charset-normalizer 可覆盖绝大多数场景。代价是引入 pandas 依赖，但 pandas 在数据管线中几乎必然存在。

### D3: XLS 用 xlrd，XLSX 用 openpyxl

**选择**: xlrd 专读 .xls（仅支持旧格式），openpyxl 读写 .xlsx

**替代方案**:
- 全部用 pandas: 丢失公式、合并、隐藏等元数据
- 全部用 openpyxl: openpyxl 不支持 .xls
- pyxlsb: 仅支持 .xlsb，不在需求范围

**理由**: xlrd 和 openpyxl 是各自格式的事实标准库，对公式、合并区域、隐藏状态等元数据的支持最完整。两个库的 API 风格差异通过解析器适配层屏蔽。

### D4: 解析器策略模式 + 工厂路由

**选择**: 定义 `BaseParser` 抽象类，各格式实现子类（`CSVParser`、`XLSParser`、`XLSXParser`），由 `ParserFactory` 根据文件类型分发

**替代方案**:
- 单一大函数 + if-else: 简单但不可扩展
- 插件注册表: 过度设计

**理由**: 策略模式让每个解析器独立测试，新增格式只需添加子类和注册。工厂集中路由逻辑。不过度抽象。

### D5: 编码探测使用 charset-normalizer

**选择**: `charset-normalizer` 读取文件前 N 字节进行编码猜测

**替代方案**:
- chardet: 较老，速度慢，对 CJK 准确率不如 charset-normalizer
- cchardet: 快但维护状态不明

**理由**: charset-normalizer 纯 Python、无 C 扩展依赖、对中文编码（GBK/GB2312/Big5）准确率高，且是 requests 3 的默认选择。

### D6: 包结构采用 src layout

```
src/table_parsing/
├── __init__.py          # 对外暴露 parse_file, IR classes
├── ir/
│   ├── __init__.py
│   └── model.py         # Workbook, Sheet, Cell, MediaObject
├── parsers/
│   ├── __init__.py
│   ├── base.py          # BaseParser 抽象类
│   ├── csv_parser.py
│   ├── xls_parser.py
│   └── xlsx_parser.py
├── engine.py            # ParserFactory + parse_file 入口
├── config.py            # ParseConfig dataclass
└── exceptions.py        # 自定义异常
```

**理由**: src layout 防止意外从不安装的源码导入，是 Python 社区推荐实践。

### D7: 模型 API 适配层采用 OpenAI 兼容协议

**选择**: 使用 OpenAI Chat Completions 兼容格式作为模型调用协议，默认连接本地 LM Studio 端点

**配置结构**:
```python
@dataclass
class ModelApiConfig:
    base_url: str = "http://169.254.83.107:1234"  # LM Studio 本地端点
    model: str = "qwen3.5-4b"                      # 默认模型
    api_key: str = ""                               # 本地服务无需 Key
    max_concurrency: int = 6                        # 并发数
```

**替代方案**:
- 固定 SDK（如 openai SDK）: 强绑定特定厂商，本地模型适配差
- 自定义 HTTP 协议: 重复造轮子，各家 API 格式各异
- LiteLLM 代理: 额外依赖和服务

**理由**: OpenAI Chat Completions 格式已成为事实标准，LM Studio、Ollama、vLLM、Azure OpenAI 均兼容此协议。本地默认连接 LM Studio（端口 1234），零配置即可工作。后期切换到其他服务商只需改 base_url + api_key。并发控制用 `asyncio.Semaphore` 实现，轻量且精准。

**适配策略**: 抽象出 `ModelClient` 协议类，默认实现为 `OpenAICompatibleClient`（直连 HTTP），后期可扩展其他实现。

### D8: 包结构调整（新增模型客户端模块）

```
src/table_parsing/
├── __init__.py
├── ir/
│   ├── __init__.py
│   └── model.py
├── parsers/
│   ├── __init__.py
│   ├── base.py
│   ├── csv_parser.py
│   ├── xls_parser.py
│   └── xlsx_parser.py
├── media/                  # 新增：多媒体处理模块
│   ├── __init__.py
│   ├── extractor.py        # 媒体对象提取
│   └── understanding.py    # AI 理解客户端
├── model_client/           # 新增：模型 API 客户端
│   ├── __init__.py
│   ├── base.py             # ModelClient 协议类
│   └── openai_compat.py    # OpenAI 兼容实现
├── engine.py
├── config.py               # ParseConfig + ModelApiConfig
└── exceptions.py
```

## Risks / Trade-offs

- **[xlrd 仅支持 .xls 旧格式]** → xlrd 2.x 已移除 .xlsx 支持，XLSX 必须用 openpyxl。两者并存增加维护成本，但格式差异决定了必须如此。
- **[大文件内存]** → CSV 分块通过 pandas chunksize 解决；XLSX 大文件需 openpyxl 的 read_only 模式，但 read_only 模式下部分功能受限（如合并区域信息获取方式不同）。通过渐进式适配处理。
- **[编码误判]** → charset-normalizer 对短文件可能误判。策略：先尝试 UTF-8（成功率最高），失败后再探测。探测结果可用时记录 confidence 供下游参考。
- **[日期类型判定复杂]** → Excel 内部存储日期为浮点数，依赖 number_format 区分。openpyxl 的 `is_date` 属性可辅助但非 100% 可靠。对歧义情况记录 format 字符串，交给下游判定。
- **[本地模型可用性]** → 默认依赖 http://169.254.83.107:1234 本地 LM Studio 服务。若服务不可用，媒体 AI 理解降级跳过并记录 WARNING，不影响核心解析流程。
- **[模型响应延迟]** → 并发 6 路调用可能对本地 GPU 造成压力。通过 max_concurrency 可调降，且超时机制防止阻塞。
