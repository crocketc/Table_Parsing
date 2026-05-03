"""
创建测试用的 XLS 文件
"""

import datetime as dt
from pathlib import Path
import xlwt


def create_simple_xls(file_path: Path) -> None:
    """创建简单的 XLS 文件用于测试"""
    workbook = xlwt.Workbook()

    # 添加工作表
    sheet = workbook.add_sheet("Sheet1")

    # 添加一些数据
    sheet.write(0, 0, "Name")
    sheet.write(0, 1, "Age")
    sheet.write(0, 2, "City")

    sheet.write(1, 0, "Alice")
    sheet.write(1, 1, 30)
    sheet.write(1, 2, "New York")

    sheet.write(2, 0, "Bob")
    sheet.write(2, 1, 25)
    sheet.write(2, 2, "London")

    sheet.write(3, 0, "Charlie")
    sheet.write(3, 1, 35)
    sheet.write(3, 2, "Paris")

    # 设置文档属性
    workbook.doc_author = "Test Author"

    workbook.save(file_path)


def create_xls_with_merged_cells(file_path: Path) -> None:
    """创建带合并单元格的 XLS 文件"""
    workbook = xlwt.Workbook()
    sheet = workbook.add_sheet("Sheet1")

    # 合并第一行作为标题
    sheet.write_merge(0, 0, 0, 2, "Sales Report")

    # 添加表头
    sheet.write(2, 0, "Product")
    sheet.write(2, 1, "Q1")
    sheet.write(2, 2, "Q2")

    # 添加数据
    sheet.write(3, 0, "Widget A")
    sheet.write(3, 1, 1000)
    sheet.write(3, 2, 1200)

    # 合并产品名称单元格
    sheet.write_merge(4, 5, 0, 0, "Widget B")
    sheet.write(4, 1, 1500)
    sheet.write(4, 2, 1800)
    sheet.write(5, 1, 1600)
    sheet.write(5, 2, 1900)

    workbook.save(file_path)


def create_xls_with_multiple_sheets(file_path: Path) -> None:
    """创建多工作表的 XLS 文件"""
    workbook = xlwt.Workbook()

    # 第一个工作表
    sheet1 = workbook.add_sheet("Sheet1")
    sheet1.write(0, 0, "Data 1")
    sheet1.write(0, 1, "Value 1")
    sheet1.write(1, 0, "Item 1")
    sheet1.write(1, 1, 100)

    # 第二个工作表
    sheet2 = workbook.add_sheet("Sheet2")
    sheet2.write(0, 0, "Data 2")
    sheet2.write(0, 1, "Value 2")
    sheet2.write(1, 0, "Item 2")
    sheet2.write(1, 1, 200)

    # 第三个工作表（设置为隐藏）
    sheet3 = workbook.add_sheet("HiddenSheet")
    sheet3.write(0, 0, "Hidden Data")
    sheet3.write(0, 1, "Hidden Value")

    # 注意：xlwt 不直接支持隐藏工作表，但这在真实的 XLS 文件中是可能的
    # 我们会在测试中通过其他方式创建隐藏工作表

    workbook.save(file_path)


def create_xls_with_different_types(file_path: Path) -> None:
    """创建包含不同数据类型的 XLS 文件"""
    workbook = xlwt.Workbook()
    sheet = workbook.add_sheet("DataTypes")

    # 字符串
    sheet.write(0, 0, "Type")
    sheet.write(0, 1, "Value")

    # 数字
    sheet.write(1, 0, "Integer")
    sheet.write(1, 1, 42)

    sheet.write(2, 0, "Float")
    sheet.write(2, 1, 3.14159)

    # 布尔值
    sheet.write(3, 0, "Boolean")
    sheet.write(3, 1, True)

    # 日期
    sheet.write(4, 0, "Date")
    date_style = xlwt.XFStyle()
    date_style.num_format_str = 'YYYY-MM-DD'
    sheet.write(4, 1, dt.date(2024, 5, 3), date_style)

    # 日期时间
    sheet.write(5, 0, "DateTime")
    datetime_style = xlwt.XFStyle()
    datetime_style.num_format_str = 'YYYY-MM-DD HH:MM:SS'
    sheet.write(5, 1, dt.datetime(2024, 5, 3, 14, 30, 0), datetime_style)

    # 空白单元格
    sheet.write(6, 0, "Blank")
    sheet.write(6, 1, "")

    workbook.save(file_path)


def main():
    """创建所有测试文件"""
    test_data_dir = Path(__file__).parent / "test_data" / "xls"
    test_data_dir.mkdir(parents=True, exist_ok=True)

    print("Creating test XLS files...")

    create_simple_xls(test_data_dir / "simple.xls")
    print(f"Created: {test_data_dir / 'simple.xls'}")

    create_xls_with_merged_cells(test_data_dir / "merged_cells.xls")
    print(f"Created: {test_data_dir / 'merged_cells.xls'}")

    create_xls_with_multiple_sheets(test_data_dir / "multiple_sheets.xls")
    print(f"Created: {test_data_dir / 'multiple_sheets.xls'}")

    create_xls_with_different_types(test_data_dir / "data_types.xls")
    print(f"Created: {test_data_dir / 'data_types.xls'}")

    print("All test XLS files created successfully!")


if __name__ == "__main__":
    main()
