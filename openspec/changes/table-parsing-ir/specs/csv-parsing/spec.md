## ADDED Requirements

### Requirement: 自动字符编码探测
系统 SHALL 自动探测 CSV 文件的字符编码，优先尝试 UTF-8，失败后使用 charset-normalizer 进行智能探测。

#### Scenario: UTF-8 编码文件直接解析
- **WHEN** CSV 文件使用 UTF-8 编码
- **THEN** 系统直接成功解析，不触发额外编码探测

#### Scenario: GBK 编码文件自动探测
- **WHEN** CSV 文件使用 GBK 编码（常见于中文 Windows 系统导出）
- **THEN** 系统通过 charset-normalizer 探测到 GBK 编码并正确解析，中文内容不乱码

#### Scenario: GB2312 编码文件自动探测
- **WHEN** CSV 文件使用 GB2312 编码
- **THEN** 系统正确探测编码并解析

#### Scenario: 带 BOM 的 UTF-8 文件
- **WHEN** CSV 文件使用 UTF-8-BOM 编码（含 BOM 标记）
- **THEN** 系统正确识别并解析，BOM 标记不作为内容出现

### Requirement: 分隔符自动嗅探
系统 SHALL 自动嗅探 CSV 文件的分隔符，支持逗号、制表符、分号等常见分隔符。

#### Scenario: 逗号分隔
- **WHEN** CSV 文件使用逗号作为分隔符
- **THEN** 系统正确识别逗号为分隔符并解析

#### Scenario: 制表符分隔（TSV）
- **WHEN** CSV 文件使用制表符作为分隔符
- **THEN** 系统正确识别制表符为分隔符并解析

#### Scenario: 分号分隔
- **WHEN** CSV 文件使用分号作为分隔符（常见于欧洲区域设置）
- **THEN** 系统正确识别分号为分隔符并解析

### Requirement: 复杂字段容错解析
系统 SHALL 正确处理字段内换行、引号包裹、转义字符等复杂情况。

#### Scenario: 字段内包含换行符
- **WHEN** CSV 文件中某个字段被双引号包裹且内部包含换行符
- **THEN** 系统将该字段作为单个值解析，换行符保留在值中

#### Scenario: 字段内包含双引号
- **WHEN** CSV 文件中字段值包含转义双引号（`""`）
- **THEN** 系统正确解析为单个双引号字符

#### Scenario: 字段内包含分隔符
- **WHEN** CSV 文件中字段值包含分隔符字符但被引号包裹
- **THEN** 系统不将该分隔符视为字段分隔

### Requirement: CSV 作为单 Sheet 处理
系统 SHALL 将 CSV 文件解析为包含单个 Sheet 的 Workbook。

#### Scenario: CSV 文件的 IR 结构
- **WHEN** CSV 文件被成功解析
- **THEN** 输出的 Workbook 包含 1 个 Sheet，Sheet.name 为文件名（不含扩展名），Sheet.hidden 为 False

#### Scenario: CSV 单元格数据类型
- **WHEN** CSV 文件包含数字列、文本列、空值
- **THEN** 数字被识别为 `number` 类型，文本为 `string` 类型，空值为 `blank` 类型
