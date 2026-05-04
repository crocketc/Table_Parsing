# Table Parsing IR

统一的表格文件解析库，提供纯 Python 中间表示（IR）。

## 特性

- **多格式支持**: CSV、XLS、XLSX
- **自动编码检测**: 智能识别 GBK、UTF-8 等编码
- **高性能**: CSV 解析速度 ≥10,000 行/秒
- **统一接口**: 所有格式返回相同的 IR 表示
- **零 pandas 依赖**: IR 模型完全独立，便于集成
- **智能类型推断**: 自动识别数字、日期、布尔值
- **容错机制**: 单元格级别的错误处理
- **公式支持**: 保留 Excel 公式信息
- **合并单元格**: 正确处理合并单元格

## 安装

```bash
pip install table-parsing-ir
```

或从源码安装：

```bash
git clone <repository-url>
cd Table_Parsing
pip install -e .
```

## CLI 命令行工具

项目提供了命令行工具 `table-parse`，方便直接运行解析而无需编写 Python 代码。

### 安装 CLI 工具

```bash
# 安装 CLI 工具（包含额外依赖）
pip install -e ".[cli]"
```

### 基础用法

```bash
# 解析 CSV 文件
table-parse data.csv

# 解析 Excel 文件
table-parse report.xlsx

# 输出到文件
table-parse data.xlsx --output result.json

# 指定输出格式（JSON/YAML/CSV）
table-parse data.csv --format yaml
```

### 配置文件

CLI 工具支持配置文件 `.table-parse.yml`，按以下优先级加载：

1. 命令行 `--config` 指定的文件
2. 当前目录的 `.table-parse.yml`
3. 当前目录的 `table-parse.yml`
4. 用户主目录的 `.table-parse.yml`

**生成配置文件模板**：

```bash
table-parse --init-config
```

**配置文件示例**：

```yaml
# 输出格式：json/yaml/csv
output_format: json

# 是否格式化输出
pretty: true

# 文件编码（留空表示自动检测）
encoding: null

# 指定要解析的工作表（留空表示解析所有）
sheets: null
# sheets:
#   - "Sheet1"
#   - "Sheet2"

# 日志级别：DEBUG/INFO/WARNING/ERROR
log_level: "INFO"
```

### 高级用法

```bash
# 显示当前配置
table-parse --show-config

# 显示配置文件路径
table-parse --show-config-path

# 命令行参数覆盖配置文件
table-parse data.csv --encoding utf-8 --format yaml

# 详细输出模式
table-parse data.xlsx --verbose
```

## 快速开始

### 解析 CSV 文件

```python
from table_parsing import parse_file

# 解析 CSV 文件（自动检测编码）
workbook = parse_file("data.csv")

# 访问数据
sheet = workbook.sheets[0]
for row in sheet.cells:
    for cell in row:
        print(cell.value)
```

### 解析 Excel 文件

```python
from table_parsing import parse_file

# 解析 XLSX 文件
workbook = parse_file("report.xlsx")

# 遍历所有工作表
for sheet in workbook.sheets:
    print(f"工作表: {sheet.name}")
    print(f"行数: {sheet.max_row}, 列数: {sheet.max_col}")
```

### 访问单元格属性

```python
workbook = parse_file("data.xlsx")
sheet = workbook.sheets[0]

# 访问特定单元格
cell = sheet.cells[0][0]  # 第一行第一列

# 获取单元格信息
print(f"值: {cell.value}")
print(f"类型: {cell.data_type}")
print(f"是否为公式: {cell.is_formula}")
if cell.is_formula:
    print(f"公式: {cell.formula_text}")
```

## IR 数据模型

### Cell

单元格数据模型：

```python
@dataclass
class Cell:
    value: Union[str, int, float, bool, datetime.date, None]
    raw_value: Optional[str] = None
    data_type: Literal["number", "string", "date", "bool", "blank"] = "string"
    is_formula: bool = False
    formula_text: Optional[str] = None
    is_merged: bool = False
    merge_range: Optional[str] = None
    is_hidden: bool = False
    style: Optional[dict] = None
    embedded_media: Optional[MediaObject] = None
```

### Sheet

工作表数据模型：

```python
@dataclass
class Sheet:
    name: str
    hidden: bool = False
    max_row: int = 0
    max_col: int = 0
    cells: list[list[Cell]] = None
```

### Workbook

工作簿数据模型：

```python
@dataclass
class Workbook:
    metadata: dict[str, Any] = None
    sheets: list[Sheet] = None
```

## 高级功能

### 自动编码检测

```python
from table_parsing.parsers import CSVParser

parser = CSVParser()

# 自动检测文件编码
with open("data.csv", "rb") as f:
    content = f.read()
encoding = parser._detect_encoding(content)
print(f"检测到的编码: {encoding}")
```

### 自动分隔符检测

```python
from table_parsing.parsers import CSVParser

parser = CSVParser()

# 自动检测 CSV 分隔符
sample = "Name;Age;City\nAlice;30;NYC"
delimiter = parser._detect_delimiter(sample)
print(f"检测到的分隔符: {delimiter}")
```

### 公式处理

```python
workbook = parse_file("formulas.xlsx")
sheet = workbook.sheets[0]

# 检查单元格是否包含公式
cell = sheet.cells[0][0]
if cell.is_formula:
    print(f"公式文本: {cell.formula_text}")
    print(f"计算结果: {cell.value}")
```

### 合并单元格

```python
workbook = parse_file("merged.xlsx")
sheet = workbook.sheets[0]

# 检查合并的单元格
for row in sheet.cells:
    for cell in row:
        if cell.is_merged:
            print(f"合并范围: {cell.merge_range}")
```

## 性能

库针对性能进行了优化：

- **CSV 解析**: ≥10,000 行/秒
- **XLSX 解析**: ≥5,000 行/秒
- **内存效率**: 支持流式处理大文件

## 开发

### 运行测试

```bash
# 运行所有测试
pytest tests/

# 运行测试并查看覆盖率
pytest --cov=src/table_parsing --cov-report=html

# 运行验收测试
pytest tests/test_acceptance.py
```

### 代码质量检查

```bash
# 运行质量检查脚本
python scripts/check_quality.py

# 或手动运行各个检查
mypy src/table_parsing
pytest --cov=src/table_parsing --cov-fail-under=80
radon cc src/table_parsing -a --min C
```

### 项目结构

```
Table_Parsing/
├── src/
│   └── table_parsing/
│       ├── engine.py          # 主入口函数
│       ├── exceptions.py      # 异常定义
│       ├── config.py          # 配置管理
│       ├── ir/                # 中间表示模型
│       ├── parsers/           # 格式解析器
│       ├── media/             # 媒体提取
│       └── model_client.py    # AI 模型客户端
├── tests/                     # 测试套件
├── scripts/                   # 实用脚本
└── docs/                      # 文档
```

## 依赖

- Python >= 3.10
- charset-normalizer >= 3.0.0
- openpyxl >= 3.1.0
- xlrd >= 2.0.0
- pandas >= 2.0.0

## 开发依赖

- pytest >= 7.0
- pytest-cov >= 4.0
- mypy >= 1.0
- radon >= 6.0

## 许可证

MIT License

## 贡献

欢迎提交 Pull Request 或报告 Issue！

## 更新日志

查看 [CHANGELOG.md](CHANGELOG.md) 了解版本更新历史。
