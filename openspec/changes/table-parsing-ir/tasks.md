## 1. 项目脚手架与基础结构

- [ ] 1.1 创建 src layout 包结构：`src/table_parsing/__init__.py`、`ir/`、`parsers/`、子模块 `__init__.py`
- [ ] 1.2 创建 `pyproject.toml`，声明依赖：charset-normalizer、openpyxl、xlrd、pandas
- [ ] 1.3 创建 `src/table_parsing/exceptions.py`，定义异常层级：`TableParsingError`（基类）、`UnsupportedFormatError`、`FileFormatMismatchError`、`FileProtectedError`、`ParseError`

## 2. IR 数据模型

- [ ] 2.1 实现 `src/table_parsing/ir/model.py`：定义 `MediaObject` dataclass（type、anchor_row/col、raw_data、raw_format、description、chart_metadata）
- [ ] 2.2 实现 `Cell` dataclass（value、raw_value、data_type、is_formula、formula_text、is_merged、merge_range、is_hidden、style、embedded_media），所有字段带默认值
- [ ] 2.3 实现 `Sheet` dataclass（name、hidden、max_row、max_col、cells）
- [ ] 2.4 实现 `Workbook` dataclass（metadata、sheets），metadata 默认空 dict
- [ ] 2.5 为每个 IR 类实现 `to_dict()` 方法，支持递归序列化（datetime→ISO str、bytes→base64）
- [ ] 2.6 编写 IR 模型单元测试：验证字段默认值、data_type 合法取值、to_dict 序列化正确性

## 3. 配置系统

- [ ] 3.1 实现 `src/table_parsing/config.py`：`ParseConfig` dataclass，含 encoding、encoding_detection、extract_media、chunk_size、sheets、range 等字段，均带安全默认值
- [ ] 3.2 编写 ParseConfig 测试：默认值验证、自定义配置、字段类型校验
- [ ] 3.3 实现 `ModelApiConfig` dataclass：base_url（默认 "http://169.254.83.107:1234"）、model（默认 "qwen3.5-4b"）、api_key（默认空串）、max_concurrency（默认 6）
- [ ] 3.4 将 ModelApiConfig 作为 ParseConfig 的 model_api 字段，默认无参构造 ModelApiConfig
- [ ] 3.5 编写 ModelApiConfig 测试：默认值验证、自定义端点、并发数

## 4. 格式路由与文件识别

- [ ] 4.1 实现 `src/table_parsing/parsers/base.py`：`BaseParser` 抽象类，定义 `parse(file_path, config) -> Workbook` 接口
- [ ] 4.2 实现文件扩展名识别逻辑（不区分大小写），映射到 .csv/.xls/.xlsx
- [ ] 4.3 实现魔数校验：XLSX（PK ZIP 签名）、XLS（OLE2 签名）、CSV 跳过
- [ ] 4.4 实现 `ParserFactory`：根据文件类型返回对应 Parser 实例，不支持的格式抛出 `UnsupportedFormatError`
- [ ] 4.5 编写格式路由测试：各种扩展名映射、魔数校验通过/失败、不支持格式异常

## 5. CSV 解析器

- [ ] 5.1 实现 `src/table_parsing/parsers/csv_parser.py`：`CSVParser(BaseParser)`
- [ ] 5.2 实现编码探测逻辑：先尝试 UTF-8，失败后使用 charset-normalizer 探测，支持 GBK/GB2312/UTF-8-BOM
- [ ] 5.3 实现分隔符自动嗅探（逗号、制表符、分号）
- [ ] 5.4 基于 pandas.read_csv 解析 CSV，正确处理字段内换行/引号/转义
- [ ] 5.5 将 pandas DataFrame 行转为 IR Cell 二维数组，自动推断 data_type（number/string/blank）
- [ ] 5.6 构建单 Sheet 的 Workbook：name 取文件名，hidden=False
- [ ] 5.7 实现 chunk_size 分块读取：返回迭代器，每次 yield 一个 Workbook
- [ ] 5.8 编写 CSV 解析测试：UTF-8/GBK 编码、各种分隔符、字段内换行/引号、空文件、分块读取

## 6. XLS 解析器

- [ ] 6.1 实现 `src/table_parsing/parsers/xls_parser.py`：`XLSParser(BaseParser)`
- [ ] 6.2 使用 xlrd 打开 .xls 文件，遍历所有 Sheet（含隐藏）
- [ ] 6.3 提取单元格值并映射 data_type：xlrd 类型码→IR data_type
- [ ] 6.4 提取合并单元格区域，标记左上角和非左上角单元格
- [ ] 6.5 提取行/列隐藏状态，设置 Cell.is_hidden
- [ ] 6.6 提取文档元数据到 Workbook.metadata
- [ ] 6.7 受保护文件检测：捕获 xlrd 密码相关异常并转为 `FileProtectedError`
- [ ] 6.8 编写 XLS 解析测试：多 Sheet、合并单元格、隐藏行列、数据类型映射、受保护文件

## 7. XLSX 解析器

- [ ] 7.1 实现 `src/table_parsing/parsers/xlsx_parser.py`：`XLSXParser(BaseParser)`
- [ ] 7.2 使用 openpyxl 打开 .xlsx 文件，遍历所有 Sheet（含隐藏）
- [ ] 7.3 提取单元格值与类型映射：openpyxl 数据类型→IR data_type，日期值转 Python datetime
- [ ] 7.4 提取公式：Cell.is_formula、formula_text、缓存值
- [ ] 7.5 提取合并单元格区域：openpyxl merged_cells → Cell.merge_range + is_merged
- [ ] 7.6 提取隐藏状态：Sheet.hidden、行隐藏、列隐藏 → Cell.is_hidden
- [ ] 7.7 提取数字格式元数据到 Cell.style（number_format）
- [ ] 7.8 提取文档属性元数据到 Workbook.metadata（author、title、created、modified）
- [ ] 7.9 受保护文件检测：捕获 openpyxl 密码相关异常并转为 `FileProtectedError`
- [ ] 7.10 按需解析支持：config.sheets 过滤、config.range 区域裁剪
- [ ] 7.11 编写 XLSX 解析测试：全字段覆盖（公式、合并、隐藏、样式、元数据）、按需解析

## 8. 统一解析引擎

- [ ] 8.1 实现 `src/table_parsing/engine.py`：`parse_file(file_path, config=None) -> Workbook | Iterator[Workbook]`
- [ ] 8.2 编排流程：文件存在检查 → 格式路由 → 魔数校验 → 解析器分发 → 返回 IR
- [ ] 8.3 单元格级容错：try/except 包裹单个 Cell 构建，失败时记录 WARNING 并跳过
- [ ] 8.4 Sheet 级容错：单个 Sheet 失败时记录 ERROR 并跳过，继续解析其余 Sheet
- [ ] 8.5 在 `src/table_parsing/__init__.py` 中暴露公共 API：`parse_file`、`ParseConfig`、IR 类、异常类
- [ ] 8.6 编写引擎集成测试：CSV/XLS/XLSX 端到端解析、容错场景、配置传递

## 9. 模型 API 客户端

- [ ] 9.1 创建 `src/table_parsing/model_client/` 模块结构（__init__.py、base.py、openai_compat.py）
- [ ] 9.2 实现 `ModelClient` 协议类（typing.Protocol）：定义 `complete(messages, images) -> str` 接口
- [ ] 9.3 实现 `OpenAICompatibleClient`：基于 httpx（同步+异步），POST 到 `{base_url}/v1/chat/completions`
- [ ] 9.4 实现并发控制：asyncio.Semaphore(max_concurrency) 限流
- [ ] 9.5 处理 API Key 为空时不发 Authorization 头，非空时发 `Bearer {api_key}`
- [ ] 9.6 编写模型客户端测试：mock HTTP 调用验证请求格式、并发限制、Key 传递

## 10. 多媒体 AI 理解

- [ ] 10.1 创建 `src/table_parsing/media/` 模块（__init__.py、extractor.py、understanding.py）
- [ ] 10.2 实现 `MediaExtractor`：从 XLSX 中提取嵌入图片（openpyxl Image 对象），构建 MediaObject（raw_data、raw_format、anchor 坐标）
- [ ] 10.3 实现 `MediaUnderstanding`：遍历 Workbook 中所有 MediaObject，调用 ModelClient 批量理解
- [ ] 10.4 将模型返回的描述文本回填到 MediaObject.description
- [ ] 10.5 编写媒体理解测试：mock 模型客户端、验证 description 回填、并发调用验证

## 11. 验收与收尾

- [ ] 9.1 使用真实异构文件（含 GBK CSV、多 Sheet XLS、带公式合并 XLSX）进行端到端验收测试
- [ ] 9.2 确认 IR 模块无 pandas 依赖（import 检查）
- [ ] 9.3 代码质量检查：type hints 完整性、docstring 覆盖关键公共 API
