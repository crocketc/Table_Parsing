#!/usr/bin/env python
"""
格式路由系统演示脚本

展示如何使用格式路由系统检测和选择合适的解析器
"""

from pathlib import Path
from table_parsing.parsers import (
    FileFormat,
    get_format_by_extension,
    detect_format_by_magic_number,
    get_parser,
)


def main():
    print("=" * 60)
    print("格式路由系统演示")
    print("=" * 60)

    # 1. 演示扩展名检测
    print("\n1. 扩展名检测:")
    print("-" * 40)
    extensions = ["csv", "xlsx", "xls", "CSV", ".xlsx", "pdf", "txt"]
    for ext in extensions:
        format_type = get_format_by_extension(ext)
        status = "✓" if format_type else "✗"
        print(f"  {status} '{ext}' -> {format_type}")

    # 2. 演示魔术数字检测
    print("\n2. 魔术数字检测:")
    print("-" * 40)

    # XLSX 文件头 (ZIP 格式)
    xlsx_data = b"PK\x03\x04" + b"\x00" * 100
    print(f"  XLSX (ZIP): {detect_format_by_magic_number(xlsx_data)}")

    # XLS 文件头 (OLE2 格式)
    xls_data = b"\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1" + b"\x00" * 100
    print(f"  XLS (OLE2):  {detect_format_by_magic_number(xls_data)}")

    # 未知格式
    unknown_data = b"Hello World!"
    print(f"  未知格式:    {detect_format_by_magic_number(unknown_data)}")

    # 空数据
    empty_data = b""
    print(f"  空数据:      {detect_format_by_magic_number(empty_data)}")

    # 3. 演示工厂函数
    print("\n3. 工厂函数:")
    print("-" * 40)

    test_files = [
        "data.csv",
        "report.xlsx",
        "legacy.xls",
        Path("document.csv"),
    ]

    for file_path in test_files:
        try:
            parser = get_parser(file_path)
            print(f"  ✓ {file_path} -> {parser.__class__.__name__}")
        except ValueError as e:
            print(f"  ✗ {file_path} -> Error: {e}")

    # 4. 演示魔术数字优先于扩展名
    print("\n4. 魔术数字优先级演示:")
    print("-" * 40)
    print("  创建具有错误扩展名但正确魔术数字的文件...")

    test_cases = [
        ("wrong.csv", b"PK\x03\x04" + b"\x00" * 100, "XLSX"),
        ("wrong.txt", b"\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1" + b"\x00" * 100, "XLS"),
    ]

    for filename, content, expected in test_cases:
        test_file = Path(filename)
        test_file.write_bytes(content)

        try:
            parser = get_parser(test_file)
            actual = parser.__class__.__name__.replace("Parser", "")
            match = "✓" if actual == expected else "✗"
            print(f"  {match} {filename} (.扩展名) -> {actual} (魔术数字)")
        finally:
            test_file.unlink()

    print("\n" + "=" * 60)
    print("演示完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
