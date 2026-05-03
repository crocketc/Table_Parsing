## ADDED Requirements

### Requirement: 全量 Sheet 提取
系统 SHALL 提取 Excel 文件中的所有工作表，包括隐藏的工作表。

#### Scenario: 提取所有可见 Sheet
- **WHEN** XLSX 文件包含 3 个可见工作表
- **THEN** 输出的 Workbook.sheets 包含 3 个 Sheet 对象，每个 Sheet.hidden 为 False

#### Scenario: 包含隐藏 Sheet
- **WHEN** XLSX 文件包含 2 个可见工作表和 1 个隐藏工作表
- **THEN** 输出的 Workbook.sheets 包含 3 个 Sheet 对象，隐藏的 Sheet.hidden 为 True

#### Scenario: XLS 文件多 Sheet 提取
- **WHEN** XLS 文件包含多个工作表
- **THEN** 系统使用 xlrd 正确提取所有工作表

### Requirement: 单元格值类型正确映射
系统 SHALL 将 Excel 单元格值正确映射到 IR 的 data_type 字段。

#### Scenario: 数字类型映射
- **WHEN** 单元格包含数字值（整数或浮点数）
- **THEN** Cell.data_type 为 `"number"`，Cell.value 为 Python int 或 float

#### Scenario: 文本类型映射
- **WHEN** 单元格包含文本值
- **THEN** Cell.data_type 为 `"string"`，Cell.value 为 Python str

#### Scenario: 日期时间映射
- **WHEN** 单元格包含日期或日期时间值
- **THEN** Cell.data_type 为 `"date"`，Cell.value 为 Python datetime.datetime 或 datetime.date 对象

#### Scenario: 布尔类型映射
- **WHEN** 单元格包含布尔值（Excel 中的 TRUE/FALSE）
- **THEN** Cell.data_type 为 `"bool"`，Cell.value 为 Python bool

#### Scenario: 空单元格映射
- **WHEN** 单元格为空
- **THEN** Cell.data_type 为 `"blank"`，Cell.value 为 None

### Requirement: 合并单元格结构记录
系统 SHALL 记录所有合并单元格的区域范围，并在 IR 中标记被合并的单元格。

#### Scenario: 合并区域记录
- **WHEN** XLSX 文件包含合并区域 A1:C3
- **THEN** A1 单元格的 is_merged 为 False（左上角为合并主单元格），merge_range 为 `"A1:C3"`，value 为合并后的值；B1、C1、A2 等非左上角单元格的 is_merged 为 True，value 为 None

#### Scenario: 多个不重叠合并区域
- **WHEN** 文件包含两个不重叠的合并区域
- **THEN** 每个区域的左上角单元格和被合并单元格均正确标记

### Requirement: 公式识别与提取
系统 SHALL 识别包含公式的单元格，并提取公式原文和缓存值。

#### Scenario: 公式单元格提取
- **WHEN** 单元格包含公式 `=SUM(A1:A10)`
- **THEN** Cell.is_formula 为 True，Cell.formula_text 为 `"=SUM(A1:A10)"`，Cell.value 为公式当前缓存值

#### Scenario: 无公式的普通单元格
- **WHEN** 单元格包含普通值而非公式
- **THEN** Cell.is_formula 为 False，Cell.formula_text 为 None

### Requirement: 隐藏状态捕获
系统 SHALL 记录工作表、行、列的隐藏状态。

#### Scenario: 隐藏行中的单元格
- **WHEN** 某行被设置为隐藏
- **THEN** 该行中所有单元格的 Cell.is_hidden 为 True

#### Scenario: 隐藏列中的单元格
- **WHEN** 某列被设置为隐藏
- **THEN** 该列中所有单元格的 Cell.is_hidden 为 True

### Requirement: 数据格式元数据保留
系统 SHALL 保留单元格的原始数字格式信息。

#### Scenario: 日期格式保留
- **WHEN** 单元格具有数字格式 `YYYY-MM-DD`
- **THEN** Cell.style 中包含 `{'number_format': 'YYYY-MM-DD'}`

#### Scenario: 百分比格式保留
- **WHEN** 单元格具有百分比格式 `0.00%`
- **THEN** Cell.style 中包含 `{'number_format': '0.00%'}`

### Requirement: 文档元数据提取
系统 SHALL 提取 Excel 文件的文档属性元数据。

#### Scenario: XLSX 文档属性提取
- **WHEN** XLSX 文件包含作者、标题、创建时间等文档属性
- **THEN** Workbook.metadata 中包含 `author`、`title`、`created`、`modified` 等字段

### Requirement: 受保护文件检测
系统 SHALL 检测受密码保护的 Excel 文件并抛出特定异常。

#### Scenario: 密码保护的 XLSX 文件
- **WHEN** 尝试解析一个需要密码才能打开的 XLSX 文件
- **THEN** 系统 SHALL 抛出 `FileProtectedError` 异常，包含文件路径信息

#### Scenario: 无保护的正常文件
- **WHEN** 解析一个无密码保护的 Excel 文件
- **THEN** 正常解析，不抛出保护相关异常
