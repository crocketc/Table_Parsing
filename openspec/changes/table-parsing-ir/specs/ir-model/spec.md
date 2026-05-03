## ADDED Requirements

### Requirement: Workbook 数据结构
系统 SHALL 定义 Workbook 作为 IR 的顶层容器。

#### Scenario: Workbook 基本结构
- **WHEN** 任何文件被成功解析
- **THEN** 输出为 Workbook 对象，包含 `metadata`（dict）和 `sheets`（list[Sheet]）两个字段

#### Scenario: Workbook metadata 默认值
- **WHEN** 文件不包含任何文档属性
- **THEN** Workbook.metadata 为空 dict（非 None）

### Requirement: Sheet 数据结构
系统 SHALL 定义 Sheet 表示单个工作表。

#### Scenario: Sheet 完整字段
- **WHEN** 一个工作表被解析
- **THEN** Sheet 对象包含 `name`（str）、`hidden`（bool）、`max_row`（int）、`max_col`（int）、`cells`（list[list[Cell]]）五个字段

#### Scenario: Sheet 的 cells 为二维数组
- **WHEN** 工作表有 5 行 3 列数据
- **THEN** Sheet.cells 为包含 5 个元素的列表，每个元素为包含 3 个 Cell 的列表

#### Scenario: 空工作表
- **WHEN** 工作表完全无数据
- **THEN** Sheet.cells 为空列表，max_row 和 max_col 均为 0

### Requirement: Cell 数据结构
系统 SHALL 定义 Cell 表示单个单元格的完整信息。

#### Scenario: Cell 必备字段
- **WHEN** 任何单元格被解析
- **THEN** Cell 对象至少包含 `value`、`raw_value`、`data_type`、`is_formula`、`formula_text`、`is_merged`、`merge_range`、`is_hidden`、`style`、`embedded_media` 字段

#### Scenario: Cell 默认值
- **WHEN** 创建一个空 Cell 对象
- **THEN** value 为 None，raw_value 为 None，data_type 为 `"blank"`，is_formula 为 False，formula_text 为 None，is_merged 为 False，merge_range 为 None，is_hidden 为 False，style 为 None，embedded_media 为 None

#### Scenario: data_type 合法取值
- **WHEN** 单元格被解析
- **THEN** Cell.data_type 取值 MUST 为 `"number"` / `"string"` / `"date"` / `"bool"` / `"blank"` 之一

### Requirement: MediaObject 数据结构
系统 SHALL 定义 MediaObject 用于表示嵌入的多媒体对象。

#### Scenario: MediaObject 完整字段
- **WHEN** 提取到嵌入图片
- **THEN** MediaObject 包含 `type`、`anchor_row`、`anchor_col`、`raw_data`、`raw_format`、`description`、`chart_metadata` 字段

#### Scenario: MediaObject type 合法取值
- **WHEN** 创建 MediaObject
- **THEN** type 取值 MUST 为 `"image"` 或 `"chart"` 之一

### Requirement: IR 不依赖 pandas
系统 SHALL 确保 IR 模型为纯 Python dataclass，不导入或依赖 pandas。

#### Scenario: IR 模块导入检查
- **WHEN** 导入 `table_parsing.ir.model` 模块
- **THEN** 该模块的依赖中不包含 pandas 或任何 pandas 子模块

### Requirement: IR 可序列化为 dict
系统 SHALL 支持将 IR 对象递归转换为原生 dict/list 结构。

#### Scenario: Workbook 转 dict
- **WHEN** 调用 Workbook 的 `to_dict()` 方法
- **THEN** 返回一个嵌套的 dict/list 结构，所有 dataclass 被展开为 dict，datetime 转为 ISO 格式字符串，bytes 转为 base64 字符串
