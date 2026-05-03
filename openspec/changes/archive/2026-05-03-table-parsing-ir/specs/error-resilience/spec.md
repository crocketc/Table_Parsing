## ADDED Requirements

### Requirement: 单元格级容错
系统 SHALL 在单个单元格读取失败时不中断整体解析，采用跳过并记录告警的策略。

#### Scenario: 单个单元格损坏
- **WHEN** 解析过程中某个单元格的值无法读取（如数据损坏）
- **THEN** 该单元格被标记为 Cell.data_type="blank"、value=None，其余单元格正常解析，系统记录一条 WARNING 级别日志

#### Scenario: 多个单元格失败
- **WHEN** 文件中有多个单元格读取失败
- **THEN** 所有失败单元格均被跳过并逐个记录日志，解析不中断

### Requirement: Sheet 级容错
系统 SHALL 在单个工作表解析失败时尝试继续解析其他工作表。

#### Scenario: 一个 Sheet 损坏
- **WHEN** Excel 文件中有 3 个工作表，其中 1 个严重损坏无法解析
- **THEN** 其余 2 个工作表正常解析并包含在 Workbook.sheets 中，损坏的 Sheet 在 Workbook.metadata 中记录错误信息

### Requirement: 明确的异常层级
系统 SHALL 定义清晰的异常层级，供上游区分不同类型的失败。

#### Scenario: 异常类型区分
- **WHEN** 发生解析错误
- **THEN** 系统抛出的异常 MUST 是以下之一：`UnsupportedFormatError`（不支持的格式）、`FileFormatMismatchError`（格式不匹配）、`FileProtectedError`（文件受保护）、`ParseError`（通用解析错误）

#### Scenario: 异常包含上下文信息
- **WHEN** 抛出任何解析异常
- **THEN** 异常对象 SHALL 包含 `file_path` 和 `detail` 属性，提供足够的诊断信息

### Requirement: 日志记录
系统 SHALL 在解析过程中通过标准 logging 模块记录关键事件。

#### Scenario: 编码探测日志
- **WHEN** 系统对 CSV 文件进行编码探测
- **THEN** 记录 INFO 级别日志，包含探测到的编码名称和置信度

#### Scenario: 单元格失败日志
- **WHEN** 单个单元格解析失败
- **THEN** 记录 WARNING 级别日志，包含单元格坐标（行号、列号）和错误原因
