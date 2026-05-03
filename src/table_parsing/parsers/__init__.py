"""
格式解析器模块

提供统一的表格文件解析接口，支持 CSV、XLSX、XLS 格式
"""

# 基础解析器
from .base import BaseParser

# 格式枚举和注册表
from .registry import FileFormat, detect_format_by_magic_number, get_format_by_extension

# 工厂函数
from .factory import get_parser

# 具体解析器（将在后续任务中完整实现）
from .csv_parser import CSVParser
from .xlsx_parser import XLSXParser
from .xls_parser import XLSParser

__all__ = [
    # 基础
    "BaseParser",
    # 枚举和注册表
    "FileFormat",
    "get_format_by_extension",
    "detect_format_by_magic_number",
    # 工厂
    "get_parser",
    # 解析器
    "CSVParser",
    "XLSXParser",
    "XLSParser",
]
