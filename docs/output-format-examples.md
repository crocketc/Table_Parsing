# Table Parsing IR - 解析输出格式样例

本文档展示 `parse_file()` 解析各种格式文件后的实际输出格式。

---

## 1. CSV 文件解析输出

### 输入文件 (`demo.csv`)
```csv
姓名,年龄,部门
张三,25,技术部
李四,30,市场部
```

### 解析代码
```python
from table_parsing import parse_file

workbook = parse_file('demo.csv')
sheet = workbook.sheets[0]
```

### 输出结构
```python
# Workbook 对象
Workbook(
    metadata={
        'source_file': 'C:\\...\\demo.csv',
        'file_format': 'csv',
        'parser': 'CSVParser'
    },
    sheets=[
        Sheet(
            name='demo',
            hidden=False,
            max_row=3,
            max_col=3,
            cells=[
                # Row 1 (标题行)
                [
                    Cell(value='姓名', data_type='string', ...),
                    Cell(value='年龄', data_type='string', ...),
                    Cell(value='部门', data_type='string', ...)
                ],
                # Row 2
                [
                    Cell(value='张三', data_type='string', ...),
                    Cell(value=25, data_type='number', ...),
                    Cell(value='技术部', data_type='string', ...)
                ],
                # Row 3
                [
                    Cell(value='李四', data_type='string', ...),
                    Cell(value=30, data_type='number', ...),
                    Cell(value='市场部', data_type='string', ...)
                ]
            ]
        )
    ]
)
```

### 访问数据的方式
```python
# 方式 1: 直接访问
value = sheet.cells[0][0].value  # '姓名'

# 方式 2: 遍历所有行
for row in sheet.cells:
    for cell in row:
        print(cell.value, cell.data_type)

# 方式 3: 序列化为字典
import json
data = workbook.to_dict()
print(json.dumps(data, ensure_ascii=False, indent=2))
```

---

## 2. XLSX 文件解析输出（含公式和合并单元格）

### 输入文件结构
- A1:D1 合并标题行
- D 列包含公式 `=SUM(B2:C2)`

### 解析后的关键字段

#### 公式单元格
```python
# D2 单元格（公式）
Cell(
    value='=SUM(B2:C2)',           # 公式原文（因为 data_only=False）
    raw_value='=SUM(B2:C2)',
    data_type='string',
    is_formula=True,               # ✅ 公式标记
    formula_text='SUM(B2:C2)',      # ✅ 去掉 = 的公式文本
    is_merged=False,
    merge_range=None
)
```

#### 合并单元格
```python
# A1 单元格（合并区域的左上角）
Cell(
    value='产品',
    is_merged=True,                # ✅ 合并标记
    merge_range='A1:D1'            # ✅ 合并范围
)

# B1 单元格（合并区域内的非左上角）
Cell(
    value='Q1',
    is_merged=False,               # ❌ 非左上角不标记为合并
    merge_range=None
)
```

#### 完整 Sheet 结构
```python
Sheet(
    name='销售数据',
    hidden=False,
    max_row=4,
    max_col=4,
    cells=[
        [
            Cell(value='产品', is_merged=True, merge_range='A1:D1'),
            Cell(value='Q1', ...),
            Cell(value='Q2', ...),
            Cell(value='总计', ...)
        ],
        [
            Cell(value='产品A', ...),
            Cell(value=100, data_type='number', ...),
            Cell(value=200, data_type='number', ...),
            Cell(
                value='=SUM(B2:C2)',
                is_formula=True,
                formula_text='SUM(B2:C2)',
                ...
            )
        ],
        # ... 更多行
    ]
)
```

---

## 3. Cell 字段完整说明

### 所有可用字段
```python
Cell(
    # 值相关
    value: Any,                      # 解析后的值（可能被类型转换）
    raw_value: str | None,            # 原始字符串值
    
    # 类型相关
    data_type: Literal["number", "string", "date", "bool", "blank"],
    
    # 公式相关
    is_formula: bool,                # 是否为公式
    formula_text: str | None,         # 公式原文（无 = 前缀）
    
    # 合并相关
    is_merged: bool,                 # 是否为合并区域的左上角
    merge_range: str | None,          # 合并范围（如 "A1:B3"）
    
    # 隐藏相关
    is_hidden: bool,                 # 是否在隐藏的行或列中
    
    # 样式相关
    style: dict | None,               # 样式信息
    # 例如: {"number_format": "0.00", "font": "Arial"}
    
    # 媒体相关
    embedded_media: MediaObject | None  # 嵌入的图片/图表
)
```

### 字段使用示例
```python
# 获取值
value = cell.value

# 检查是否为公式
if cell.is_formula:
    print(f"公式: {cell.formula_text}")

# 检查是否为合并单元格左上角
if cell.is_merged:
    print(f"合并范围: {cell.merge_range}")

# 检查数字格式
if cell.style and "number_format" in cell.style:
    print(f"格式: {cell.style['number_format']}")
```

---

## 4. to_dict() 序列化输出

### 序列化功能
```python
data = workbook.to_dict()
```

### 输出格式（JSON 示例）
```json
{
  "metadata": {
    "source_file": "demo.csv",
    "file_format": "csv",
    "parser": "CSVParser"
  },
  "sheets": [
    {
      "name": "demo",
      "hidden": false,
      "max_row": 3,
      "max_col": 3,
      "cells": [
        [
          {
            "value": "姓名",
            "raw_value": "姓名",
            "data_type": "string",
            "is_formula": false,
            "formula_text": null,
            "is_merged": false,
            "merge_range": null,
            "is_hidden": false,
            "style": null,
            "embedded_media": null
          },
          {
            "value": 25,
            "raw_value": "25",
            "data_type": "number",
            ...
          }
        ]
      ]
    }
  ]
}
```

### 特殊类型转换
- **datetime** → ISO 8601 字符串: `"2024-05-03T12:30:45"`
- **bytes** → Base64 字符串: `"SGVsbG8gV29ybGQ="`
- **MediaObject** → 递归序列化，包含 `raw_data` (base64)

---

## 5. 常见访问模式

### 遍历所有单元格
```python
for sheet in workbook.sheets:
    for row_idx, row in enumerate(sheet.cells):
        for col_idx, cell in enumerate(row):
            print(f"({row_idx}, {col_idx}): {cell.value} ({cell.data_type})")
```

### 查找特定数据类型
```python
# 查找所有公式
formulas = []
for sheet in workbook.sheets:
    for row in sheet.cells:
        for cell in row:
            if cell.is_formula:
                formulas.append(cell.formula_text)
```

### 提取特定列
```python
# 提取第 1 列（A 列）
column_a = [row[0].value for row in sheet.cells if len(row) > 0]

# 提取第 2 行
row_2 = [cell.value for cell in sheet.cells[1] if len(sheet.cells) > 1]
```

### 过滤非空单元格
```python
non_empty = [
    cell for row in sheet.cells
    for cell in row
    if cell.data_type != "blank" and cell.value is not None
]
```

---

## 6. 错误处理输出

### 文件不存在
```python
from table_parsing.exceptions import UnsupportedFormatError

try:
    workbook = parse_file('nonexistent.doc')
except FileNotFoundError as e:
    print(f"文件不存在: {e}")
```

### 格式不支持
```python
try:
    workbook = parse_file('document.doc')
except UnsupportedFormatError as e:
    print(f"不支持的格式: {e}")
    # 输出: Unsupported format: .doc. Supported formats: .csv, .xls, .xlsx
```

### 文件受保护
```python
from table_parsing.exceptions import FileProtectedError

try:
    workbook = parse_file('protected.xls')
except FileProtectedError as e:
    print(f"文件受保护: {e}")
```

---

## 7. 配置选项影响

### 指定编码
```python
from table_parsing import parse_file, ParseConfig

config = ParseConfig(encoding='gbk')
workbook = parse_file('gbk_file.csv', config=config)
```

### 只解析特定 Sheet
```python
config = ParseConfig(sheets=['Sheet1', 'Sheet2'])
workbook = parse_file('multi.xlsx', config=config)
```

### 提取媒体对象
```python
config = ParseConfig(extract_media=True)
workbook = parse_file('with_images.xlsx', config=config)

# 访问嵌入的图片
for sheet in workbook.sheets:
    for row in sheet.cells:
        for cell in row:
            if cell.embedded_media:
                print(f"发现图片: {cell.embedded_media.raw_format}")
```

---

## 8. 性能对比示例

### 小文件 (< 1MB)
```python
import time

start = time.time()
workbook = parse_file('small.csv')
elapsed = time.time() - start

print(f"解析耗时: {elapsed:.3f} 秒")
# 典型输出: 解析耗时: 0.015 秒
```

### 大文件分块读取
```python
config = ParseConfig(chunk_size=10000)

# 方式 1: 分块迭代
for chunk_workbook in parser.parse_chunked('large.csv', config):
    print(f"处理 {chunk_workbook.sheets[0].max_row} 行")

# 方式 2: 使用迭代器（内存友好）
chunks = parse_file('large.csv', config=config)  # 返回 Iterator[Workbook]
```

---

**总结**: Table Parsing IR 的输出是一个**纯 Python dataclass 结构**，可以通过属性访问、循环遍历、序列化为 JSON 等多种方式使用。所有原始信息（公式、合并区域、隐藏状态、样式）都被保留。
