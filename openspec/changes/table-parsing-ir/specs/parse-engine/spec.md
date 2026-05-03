## ADDED Requirements

### Requirement: 统一解析入口
系统 SHALL 提供 `parse_file()` 函数作为唯一的公共解析入口。

#### Scenario: 基本调用
- **WHEN** 调用 `parse_file("data/report.xlsx")`
- **THEN** 系统自动识别格式、选择解析器、返回 Workbook 对象

#### Scenario: 带配置调用
- **WHEN** 调用 `parse_file("data/report.csv", config=ParseConfig(encoding="gbk"))`
- **THEN** 系统使用指定配置进行解析

### Requirement: 按需解析接口
系统 SHALL 支持调用方指定解析特定 Sheet 或单元格区域。

#### Scenario: 指定 Sheet 解析
- **WHEN** 调用 `parse_file("data.xlsx", config=ParseConfig(sheets=["Sheet1"]))`
- **THEN** 仅解析 Sheet1，Workbook.sheets 仅包含 1 个 Sheet

#### Scenario: 指定矩形区域解析
- **WHEN** 调用 `parse_file("data.xlsx", config=ParseConfig(range="Sheet1!A1:Z100"))`
- **THEN** 仅提取指定区域内的单元格

### Requirement: 大文件分块读取
系统 SHALL 对大型 CSV 文件提供分批读取能力。

#### Scenario: CSV 大文件分块
- **WHEN** 调用 `parse_file("large.csv", config=ParseConfig(chunk_size=10000))`
- **THEN** 系统返回一个迭代器，每次产出包含 10000 行数据的 Workbook 块

#### Scenario: 未指定 chunk_size 时全量读取
- **WHEN** 调用 `parse_file("large.csv")`（未指定 chunk_size）
- **THEN** 系统全量读取并返回单个 Workbook

### Requirement: 解析器工厂路由
系统 SHALL 使用工厂模式根据文件类型自动选择解析器。

#### Scenario: 工厂创建 CSV 解析器
- **WHEN** 文件类型被识别为 CSV
- **THEN** 工厂返回 CSVParser 实例

#### Scenario: 工厂创建 XLS 解析器
- **WHEN** 文件类型被识别为 XLS
- **THEN** 工厂返回 XLSParser 实例

#### Scenario: 工厂创建 XLSX 解析器
- **WHEN** 文件类型被识别为 XLSX
- **THEN** 工厂返回 XLSXParser 实例
