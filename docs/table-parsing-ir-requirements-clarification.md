# Table Parsing IR - 需求澄清文档

> 本文档补充 OpenSpec 规格体系中的非功能需求、验收标准、外部依赖风险、错误处理边界和可观测性需求，与 `proposal.md`、`design.md`、`specs/` 形成互补。

**文档版本**: v1.0
**创建日期**: 2026-05-03
**状态**: 待审核

---

## 1. 执行摘要

### 1.1 项目定位

本模块是表格数据处理管线的**解析层**，负责将异构表格文件转换为统一的中间表示（IR）。

| 维度 | 说明 |
|------|------|
| **上游** | 各种来源的 CSV/XLS/XLSX 文件（ERP 导出、手工录入、历史系统迁移等） |
| **本模块** | 提供统一解析接口，输出纯 Python dataclass IR |
| **下游** | 数据清洗、分类、入库、向量化模块 |

### 1.2 核心能力速览

| Capability | 一句话描述 | 优先级 | 依赖项 |
|-----------|-----------|--------|--------|
| **format-routing** | 扩展名+魔数智能识别文件格式，自动分发到对应解析器 | P0 | 无 |
| **csv-parsing** | 编码探测+分隔符嗅探稳健解析，支持大文件分块 | P0 | pandas, charset-normalizer |
| **excel-parsing** | XLS/XLSX 全量元数据提取（公式/合并/隐藏/样式） | P0 | xlrd, openpyxl |
| **ir-model** | 纯 dataclass IR 结构，无 pandas 依赖，支持序列化 | P0 | 无 |
| **parse-engine** | 统一入口 `parse_file()` + 容错编排 + 格式路由 | P0 | 所有解析器 |
| **error-resilience** | 单元格级容错 + Sheet 级降级，记录详细日志 | P0 | 无 |
| **config-system** | 配置驱动功能开关（编码/媒体/分块/模型 API） | P0 | 无 |

---

## 2. 非功能需求

### 2.1 性能指标

| 指标 | 目标值 | 测量方法 | 备注 |
|------|--------|---------|------|
| **CSV 解析吞吐** | ≥ 10,000 行/秒 | 100MB CSV 文件计时 | 纯文本数据，不含复杂引号 |
| **XLSX 解析延迟** | ≤ 5 秒/10MB | 中等大小文件端到端 | 含元数据提取（公式/合并/隐藏） |
| **内存占用** | ≤ 文件大小 × 3 | 峰值 RSS 测量 | CSV 分块模式下更低 |
| **并发安全性** | 支持多进程读取 | 无共享状态设计 | IR 对象不可变（frozen dataclass） |
| **编码探测延迟** | ≤ 100ms/文件 | charset-normalizer 调用计时 | 仅在 encoding_detection=True 时 |

### 2.2 可靠性要求

#### 容错边界

| 级别 | 范围 | 处理策略 |
|------|------|---------|
| **单元格级** | 单个单元格解析失败 | 跳过该单元格，`value` 设为 `None`，记录 WARNING |
| **Sheet 级** | 单个 Sheet 解析失败 | 跳过该 Sheet，记录 ERROR，继续处理其余 Sheet |
| **文件级** | 文件格式不支持/损坏 | 向上抛出异常，终止解析 |

#### 降级策略

| 场景 | 降级行为 | 用户可见性 |
|------|---------|-----------|
| **LM Studio 不可用** | 跳过媒体理解，`embedded_media` 为 `None` | WARNING 日志 |
| **XLSX read_only 模式限制** | 合并区域信息获取受限，`merge_range` 为 `None` | WARNING 日志 |
| **编码探测失败** | 回退到 UTF-8 或用户指定编码 | WARNING 日志 |
| **媒体提取失败** | `embedded_media` 为 `None` | WARNING 日志 |

#### 数据完整性

- **公式**：必须提取 `is_formula`、`formula_text`、缓存值
- **合并区域**：标记 `is_merged=True`，`merge_range` 记录区域范围
- **隐藏状态**：`Cell.is_hidden` 正确反映行/列隐藏状态
- **日期类型**：统一转换为 Python `datetime` 对象
- **元数据**：`Workbook.metadata` 记录文档属性（作者/标题/创建时间等）

### 2.3 可维护性标准

| 指标 | 目标值 | 验证方法 |
|------|--------|---------|
| **类型覆盖率** | ≥ 90% | 使用 `mypy --strict` 静态检查 |
| **单元测试覆盖率** | ≥ 80% | 使用 `pytest-cov` 测量 |
| **公共 API 文档化** | 100% | 所有 `__init__.py` 暴露的 API 必须有 docstring |
| **代码复杂度** | 单函数 McCabe 复杂度 ≤ 10 | 使用 `radon` 测量 |

---

## 3. 验收标准矩阵

### 3.1 format-routing 验收

| 场景 | 验收条件 | 验证方法 | 优先级 |
|------|---------|---------|--------|
| 正常扩展名 | .csv/.xls/.xlsx 正确路由到对应解析器 | 单元测试 `test_format_routing_normal_extensions` | P0 |
| 大小写混合 | .CSV/.Xls/.XLSX 正常识别 | 单元测试 `test_format_routing_case_insensitive` | P0 |
| 错误扩展名 | .doc/.txt 抛出 `UnsupportedFormatError` | 单元测试 `test_format_routing_unsupported_format` | P0 |
| 魔数校验 | 伪造扩展名（.txt 实为 XLSX）被魔数拦截 | 集成测试 `test_magic_number_override` | P1 |
| 无扩展名 | 根据魔数推断文件类型 | 集成测试 `test_extensionless_file` | P1 |

### 3.2 csv-parsing 验收

| 场景 | 验收条件 | 验证方法 | 优先级 |
|------|---------|---------|--------|
| GBK 编码 | 中文字符正确解析，无乱码 | 真实文件测试 `test_csv_gbk_encoding` | P0 |
| GB2312 编码 | 中文字符正确解析 | 真实文件测试 `test_csv_gb2312_encoding` | P0 |
| UTF-8-BOM | 正确识别并处理 BOM | 单元测试 `test_csv_utf8_bom` | P0 |
| 分号分隔符 | 自动识别并解析 | 真实文件测试 `test_csv_semicolon_delimiter` | P0 |
| Tab 分隔符 | 自动识别并解析 | 真实文件测试 `test_csv_tab_delimiter` | P0 |
| 字段内换行 | 引号包裹的换行正确处理 | 真实文件测试 `test_csv_embedded_newlines` | P0 |
| 字段内引号 | 转义引号正确处理 | 真实文件测试 `test_csv_escaped_quotes` | P0 |
| 空文件 | 返回空 Workbook，不报错 | 单元测试 `test_csv_empty_file` | P0 |
| 分块读取 | chunk_size 正确分段，每段返回完整 Workbook | 单元测试 `test_csv_chunked_reading` | P0 |

### 3.3 excel-parsing 验收

| 场景 | 验收条件 | 验证方法 | 优先级 |
|------|---------|---------|--------|
| XLS 公式提取 | `is_formula=True`，`formula_text` 有值 | 真实文件测试 `test_xls_formula_extraction` | P0 |
| XLSX 公式提取 | `is_formula=True`，`formula_text` 有值，缓存值正确 | 真实文件测试 `test_xlsx_formula_extraction` | P0 |
| 合并区域 | `is_merged=True`，`merge_range` 正确（如 "A1:B3"） | 真实文件测试 `test_merged_cells` | P0 |
| 隐藏行列 | `is_hidden=True` | 真实文件测试 `test_hidden_rows_columns` | P0 |
| 隐藏 Sheet | `Sheet.hidden=True` | 真实文件测试 `test_hidden_sheet` | P0 |
| 受保护文件 | 抛出 `FileProtectedError` | 真实文件测试 `test_protected_file` | P0 |
| 数字格式 | `Cell.style.number_format` 记录格式字符串 | 真实文件测试 `test_number_format` | P1 |
| 文档元数据 | `Workbook.metadata` 包含 author/title/created/modified | 真实文件测试 `test_document_metadata` | P1 |
| 按需解析（sheets 过滤） | 仅解析指定的 Sheet | 集成测试 `test_selective_sheets` | P1 |
| 按需解析（range 裁剪） | 仅解析指定区域 | 集成测试 `test_range_cropping` | P2 |

### 3.4 ir-model 验收

| 场景 | 验收条件 | 验证方法 | 优先级 |
|------|---------|---------|--------|
| 无 pandas 依赖 | `import table_parsing.ir.model` 不导入 pandas | 静态分析 `test_ir_no_pandas_import` | P0 |
| to_dict 序列化 | `datetime` → ISO 字符串，`bytes` → base64 | 单元测试 `test_ir_to_dict_serialization` | P0 |
| data_type 取值 | 仅限 `number`/`string`/`date`/`bool`/`blank` | 单元测试 `test_cell_data_type_validation` | P0 |
| 默认值 | 所有字段有合理默认值 | 单元测试 `test_ir_default_values` | P0 |
| 嵌套结构 | `Workbook` → `Sheet` → `Cell` 递归正确 | 单元测试 `test_ir_nested_structure` | P0 |

### 3.5 parse-engine 验收

| 场景 | 验收条件 | 验证方法 | 优先级 |
|------|---------|---------|--------|
| 端到端 CSV 解析 | 真实 CSV 文件 → 完整 IR | 集成测试 `test_end_to_end_csv` | P0 |
| 端到端 XLS 解析 | 真实 XLS 文件 → 完整 IR | 集成测试 `test_end_to_end_xls` | P0 |
| 端到端 XLSX 解析 | 真实 XLSX 文件 → 完整 IR | 集成测试 `test_end_to_end_xlsx` | P0 |
| 单元格容错 | 错误单元格跳过并记录 WARNING | 故障注入测试 `test_cell_fault_tolerance` | P0 |
| Sheet 容错 | 错误 Sheet 跳过并记录 ERROR | 故障注入测试 `test_sheet_fault_tolerance` | P0 |
| 配置传递 | ParseConfig 正确传递到解析器 | 集成测试 `test_config_propagation` | P0 |

### 3.6 config-system 验收

| 场景 | 验收条件 | 验证方法 | 优先级 |
|------|---------|---------|--------|
| 默认配置 | 无参构造使用所有默认值 | 单元测试 `test_default_config` | P0 |
| 媒体提取开关 | `extract_media=False` 时 `embedded_media` 为 `None` | 单元测试 `test_media_extraction_toggle` | P0 |
| 编码指定 | `encoding="gbk"` 时跳过探测 | 单元测试 `test_explicit_encoding` | P0 |
| 编码探测开关 | `encoding_detection=False` 时不探测 | 单元测试 `test_encoding_detection_toggle` | P0 |
| 分块配置 | `chunk_size=10000` 正确分段 | 单元测试 `test_chunk_size_config` | P0 |
| 模型 API 默认配置 | LM Studio 端点、qwen3.5-4b、空 Key、并发 6 | 单元测试 `test_default_model_api_config` | P0 |
| 模型 API 自定义配置 | 自定义端点/模型/Key/并发正确设置 | 单元测试 `test_custom_model_api_config` | P0 |

---

## 4. 外部依赖与风险缓解

### 4.1 LM Studio 本地服务依赖

**风险描述**：
- 默认配置依赖 `http://169.254.83.107:1234` 本地 LM Studio 服务
- 服务不可用时，媒体 AI 理解功能失败

**影响范围**：
- 仅影响 `extract_media=True` 时的媒体内容理解
- 不影响核心解析功能（CSV/XLS/XLSX 解析仍正常工作）

**缓解措施**：

| 措施 | 实现方式 | 优先级 |
|------|---------|--------|
| **降级策略** | 连接失败时跳过媒体理解，记录 WARNING 日志 | P0 |
| **超时控制** | HTTP 请求设置 30 秒超时 | P0 |
| **可配置性** | `base_url` 可通过 `ModelApiConfig` 调整 | P0 |
| **快速失败** | 首条请求失败后，后续请求不再重试 | P1 |
| **健康检查** | （后期扩展）首条请求前先发 ping 测试 | P2 |

**代码示例**：
```python
# 降级策略实现
try:
    description = await model_client.complete(messages, images)
    media_object.description = description
except (ConnectError, TimeoutError):
    logger.warning(f"LM Studio unavailable, skipping media understanding for {media_object}")
    media_object.description = None  # 降级
```

### 4.2 网络依赖

**风险描述**：
- 媒体理解需要 HTTP 调用，网络抖动可能导致延迟
- 并发请求可能对本地 GPU 造成压力

**影响范围**：
- 仅影响媒体 AI 理解的性能
- 不影响核心解析功能

**缓解措施**：

| 措施 | 实现方式 | 优先级 |
|------|---------|--------|
| **重试策略** | 仅对连接错误重试 1 次，逻辑错误不重试 | P0 |
| **并发限制** | 默认 `max_concurrency=6`，可通过配置调整 | P0 |
| **超时保护** | 每请求 30 秒超时 | P0 |
| **异步隔离** | 使用 `asyncio.Semaphore` 限流，不阻塞主线程 | P0 |

### 4.3 编码探测失败

**风险描述**：
- `charset-normalizer` 对短文件（< 100 字节）可能误判
- 二进制文件伪装成 CSV 可能导致探测卡死

**影响范围**：
- CSV 解析可能产生乱码
- 严重时可能导致解析失败

**缓解措施**：

| 措施 | 实现方式 | 优先级 |
|------|---------|--------|
| **UTF-8 优先** | 先尝试 UTF-8（成功率最高），失败后再探测 | P0 |
| **用户覆盖** | `encoding` 参数可显式指定，跳过探测 | P0 |
| **置信度记录** | 探测结果记录 `confidence` 供下游参考 | P1 |
| **文件大小检查** | < 100 字节文件直接使用 UTF-8 | P2 |
| **超时保护** | 探测设置 5 秒超时 | P2 |

### 4.4 大文件内存压力

**风险描述**：
- 100MB+ CSV 文件全量加载可能导致 OOM
- XLSX 大文件解析可能占用大量内存

**影响范围**：
- 大文件解析失败或进程崩溃

**缓解措施**：

| 措施 | 实现方式 | 优先级 |
|------|---------|--------|
| **分块读取** | CSV 支持 `chunk_size` 参数，返回迭代器 | P0 |
| **read_only 模式** | XLSX 使用 openpyxl 的 `read_only=True` | P0 |
| **流式处理** | 分块模式下支持逐块处理，不累积 | P1 |
| **内存监控** | （后期扩展）峰值内存超过阈值时告警 | P2 |

---

## 5. 错误处理边界

### 5.1 致命错误（解析终止）

| 错误类型 | 异常类 | 触发条件 | 处理策略 |
|---------|--------|---------|---------|
| 文件不存在 | `FileNotFoundError` | 路径不存在 | 向上抛出，由调用方处理 |
| 不支持的格式 | `UnsupportedFormatError` | 扩展名和魔数都不匹配 | 向上抛出，建议用户检查文件 |
| 文件受保护 | `FileProtectedError` | XLS/XLSX 有密码保护 | 向上抛出，建议用户解锁 |
| 格式不匹配 | `FileFormatMismatchError` | 扩展名与魔数不一致 | 向上抛出，按魔数格式解析 |

**用户可见性**：
- 异常消息包含文件路径和失败原因
- 建议用户采取的修复措施

### 5.2 容错错误（记录并继续）

| 错误类型 | 日志级别 | 触发条件 | 处理策略 |
|---------|---------|---------|---------|
| 单个单元格解析失败 | WARNING | 单元格值格式异常（如无效日期） | 跳过该单元格，`value` 设为 `None` |
| 单个 Sheet 解析失败 | ERROR | Sheet 数据损坏 | 跳过该 Sheet，继续处理其余 |
| 编码探测失败 | WARNING | 无法确定文件编码 | 尝试备选编码或回退到 UTF-8 |
| 媒体提取失败 | WARNING | 图片数据损坏或格式不支持 | `embedded_media` 设为 `None` |

**日志格式示例**：
```
WARNING: Failed to parse cell B5 in Sheet1: invalid date format "2024-13-45", skipping
ERROR: Failed to parse Sheet2: corrupted data at row 100, skipping sheet
WARNING: Encoding detection failed for file.csv, falling back to UTF-8
```

### 5.3 降级场景

| 场景 | 触发条件 | 降级行为 | 用户可见性 |
|------|---------|---------|-----------|
| LM Studio 不可用 | 连接失败/超时 | 跳过媒体理解，`description` 为 `None` | WARNING 日志 |
| XLSX read_only 模式限制 | 合并区域信息获取受限 | `merge_range` 设为 `None` | WARNING 日志 |
| 媒体提取失败 | 图片数据损坏 | `embedded_media` 设为 `None` | WARNING 日志 |
| 编码探测失败 | 短文件/二进制伪装 | 回退到 UTF-8 或用户指定编码 | WARNING 日志 |

### 5.4 异常层级设计

```
TableParsingError (基类)
├── UnsupportedFormatError (格式不支持)
├── FileFormatMismatchError (扩展名与魔数不匹配)
├── FileProtectedError (文件受密码保护)
└── ParseError (通用解析错误)
```

---

## 6. 可观测性需求

### 6.1 日志要求

#### 日志级别使用规范

| 级别 | 使用场景 | 示例 |
|------|---------|------|
| **DEBUG** | 详细的解析过程（格式识别、编码探测结果） | `"Detected encoding: GBK (confidence: 0.98)"` |
| **INFO** | 关键操作开始/结束（文件解析完成） | `"Parsed file.xlsx: 3 sheets, 1500 cells in 2.3s"` |
| **WARNING** | 容错处理（单元格跳过、降级） | `"Failed to parse cell B5: invalid date format, skipping"` |
| **ERROR** | 部分失败（Sheet 跳过） | `"Failed to parse Sheet2: corrupted data, skipping sheet"` |

#### 关键日志点

| 位置 | 日志内容 | 级别 |
|------|---------|------|
| 文件开始解析 | `"Starting to parse: {file_path}"` | INFO |
| 格式识别结果 | `"Detected format: {format} by magic number"` | DEBUG |
| 编码探测结果 | `"Detected encoding: {encoding} (confidence: {confidence})"` | DEBUG |
| Sheet 解析完成 | `"Parsed sheet {name}: {rows} rows, {cols} cols"` | INFO |
| 单元格跳过 | `"Skipping cell {addr}: {reason}"` | WARNING |
| Sheet 跳过 | `"Skipping sheet {name}: {reason}"` | ERROR |
| 文件解析完成 | `"Parsed {file_path}: {total_sheets} sheets, {total_cells} cells in {elapsed}s"` | INFO |

### 6.2 调试接口需求

#### IR 序列化

```python
# IR 模型的 to_dict() 方法支持序列化
workbook = parse_file("data.xlsx")
data_dict = workbook.to_dict()  # 转换为原生 dict/list，便于调试输出

# datetime → ISO 格式字符串
# bytes → base64 字符串
```

#### 配置可读性

```python
# ParseConfig 支持 __repr__ 显示当前配置
config = ParseConfig(encoding="gbk", extract_media=True)
print(config)
# Output: ParseConfig(encoding='gbk', encoding_detection=True, extract_media=True, ...)
```

#### 异常上下文

```python
# 异常类包含详细的错误上下文
try:
    parse_file("data.doc")
except UnsupportedFormatError as e:
    print(e)
    # Output: "Unsupported format: .doc. Supported formats: .csv, .xls, .xlsx"
```

### 6.3 性能监控建议（后期扩展）

| 指标 | 实现方式 | 优先级 |
|------|---------|--------|
| **解析耗时** | Python `logging` 记录开始/结束时间 | P2 |
| **内存使用峰值** | `memory_profiler` 记录峰值 RSS | P2 |
| **吞吐量** | 每秒解析行数/单元格数 | P2 |
| **错误率** | 容错事件计数（WARNING/ERROR 日志统计） | P2 |

### 6.4 测试辅助接口

```python
# 提供测试辅助函数，验证 IR 结构
def assert_workbook_valid(workbook: Workbook):
    """断言 Workbook 结构合法"""
    assert workbook.metadata is not None
    assert len(workbook.sheets) > 0
    for sheet in workbook.sheets:
        assert sheet.name is not None
        assert isinstance(sheet.cells, list)
```

---

## 附录 A：术语表

| 术语 | 定义 |
|------|------|
| **IR** | Intermediate Representation，中间表示，统一的表格数据结构 |
| **魔数** | 文件开头的字节签名，用于识别真实格式（如 XLSX 的 PK ZIP 签名） |
| **容错** | 遇到错误时跳过错误部分并继续处理，而非整体失败 |
| **降级** | 功能不可用时自动回退到简化模式 |
| **分块读取** | 大文件按固定行数分段处理，避免内存溢出 |

---

## 附录 B：参考文档

- `openspec/changes/table-parsing-ir/proposal.md` — 项目提案（Why/What/Impact）
- `openspec/changes/table-parsing-ir/design.md` — 架构设计（Decisions/Risks）
- `openspec/changes/table-parsing-ir/specs/` — 详细技术规格（7 个 spec 文件）
- `openspec/changes/table-parsing-ir/tasks.md` — 实施任务清单

---

**文档维护者**：Table Parsing IR 团队
**最后更新**：2026-05-03
