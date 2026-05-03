## Why

异构表格文件（CSV/XLS/XLSX）来源于不同系统和历史版本，编码、格式、结构差异巨大。当前缺乏一个统一的解析层，导致下游数据清洗、分类、入库和向量化流程不得不反复处理各种边界情况，既脆弱又低效。需要构建一个独立的解析模块，将所有格式无损转换为统一的中间表示（IR），为整个数据管线提供干净、完整的原始数据入口。

## What Changes

- 新建 Python 包 `table_parsing`，提供统一的文件解析入口
- 定义纯 dataclass 的 IR 结构：`Workbook` → `Sheet` → `Cell` → `MediaObject`
- 实现智能格式路由：通过扩展名 + 魔数自动分发到对应解析器（CSV / XLS / XLSX）
- 实现 CSV 稳健解析：自动编码探测（GBK/GB2312 等）、分隔符嗅探、字段内换行/引号容错
- 实现 XLS/XLSX 全量提取：所有 Sheet（含隐藏）、单元格值、合并区域、公式原文
- 统一数据类型映射：数字/文本/日期/布尔/空，日期统一转 Python datetime
- 记录合并单元格结构、公式、隐藏状态等元数据，不丢失原始信息
- 提供配置驱动的能力开关（媒体提取、大文件分块等）

## Capabilities

### New Capabilities
- `format-routing`: 智能格式路由与文件类型识别，通过扩展名和魔数自动分发
- `csv-parsing`: CSV 稳健解析，含编码探测、分隔符嗅探、复杂字段容错
- `excel-parsing`: XLS/XLSX 全量解析，含 Sheet/单元格/合并/公式/隐藏状态提取
- `ir-model`: 统一中间表示（IR）数据模型定义，纯 dataclass 不依赖 pandas
- `parse-engine`: 统一解析引擎入口，协调各解析器并输出标准 IR
- `error-resilience`: 错误容错与降级处理，跳过失败单元格并记录告警
- `config-system`: 配置驱动的功能开关系统，控制解析行为和可选项

### Modified Capabilities
（全新项目，无已有能力需修改）

## Impact

- **新增依赖**: `charset-normalizer`（编码探测）、`openpyxl`（XLSX）、`xlrd`（XLS）、`pandas`（CSV 底层解析 + 大文件分块）、`httpx`（模型 API HTTP 客户端）
- **包结构**: 新建 `src/table_parsing/` 包，含 `ir/`、`parsers/`、`engine/` 子模块
- **对外接口**: 提供 `parse_file(path, config) -> Workbook` 同步入口
- **无破坏性变更**: 全新模块，不影响任何现有代码
