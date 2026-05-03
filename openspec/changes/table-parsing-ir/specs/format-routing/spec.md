## ADDED Requirements

### Requirement: 文件格式自动识别
系统 SHALL 根据文件扩展名自动识别文件类型（.csv / .xls / .xlsx），并将请求路由到对应的解析器。

#### Scenario: 通过扩展名识别 CSV 文件
- **WHEN** 输入文件路径以 `.csv` 结尾（不区分大小写）
- **THEN** 系统将文件路由到 CSV 解析器

#### Scenario: 通过扩展名识别 XLS 文件
- **WHEN** 输入文件路径以 `.xls` 结尾（不区分大小写）
- **THEN** 系统将文件路由到 XLS 解析器

#### Scenario: 通过扩展名识别 XLSX 文件
- **WHEN** 输入文件路径以 `.xlsx` 结尾（不区分大小写）
- **THEN** 系统将文件路由到 XLSX 解析器

### Requirement: 魔数校验
系统 SHALL 对文件头进行魔数校验，验证文件实际内容与扩展名声称的格式一致。

#### Scenario: XLSX 文件魔数校验通过
- **WHEN** 扩展名为 `.xlsx` 且文件头前 4 字节为 PK ZIP 签名（`50 4B 03 04`）
- **THEN** 校验通过，继续解析

#### Scenario: XLSX 文件魔数校验失败
- **WHEN** 扩展名为 `.xlsx` 但文件头不是 ZIP 签名
- **THEN** 系统 SHALL 抛出 `FileFormatMismatchError` 异常，包含期望格式和实际检测格式的描述

#### Scenario: XLS 文件魔数校验通过
- **WHEN** 扩展名为 `.xls` 且文件头为 OLE2 签名（`D0 CF 11 E0 A1 B1 1A E1`）
- **THEN** 校验通过，继续解析

#### Scenario: CSV 文件跳过魔数校验
- **WHEN** 扩展名为 `.csv`
- **THEN** 系统不进行魔数校验（CSV 是纯文本，无固定文件头）

### Requirement: 不支持的格式拒绝
系统 SHALL 对不支持的文件格式抛出明确的异常。

#### Scenario: 不支持的扩展名
- **WHEN** 输入文件扩展名不是 .csv / .xls / .xlsx 中的任一种
- **THEN** 系统 SHALL 抛出 `UnsupportedFormatError` 异常，列出当前支持的格式

#### Scenario: 文件不存在
- **WHEN** 输入路径指向的文件不存在
- **THEN** 系统 SHALL 抛出 `FileNotFoundError`
