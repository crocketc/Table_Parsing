# src/table_parsing/__init__.py
"""
Table Parsing IR - 统一的表格文件解析库

将 CSV/XLS/XLSX 文件转换为纯 Python dataclass 中间表示。
"""

from .config import ModelApiConfig, ParseConfig
from .exceptions import (
    FileFormatMismatchError,
    FileProtectedError,
    ParseError,
    TableParsingError,
    UnsupportedFormatError,
)
from .ir import MediaObject

__version__ = "0.1.0"

__all__ = [
    "TableParsingError",
    "UnsupportedFormatError",
    "FileFormatMismatchError",
    "FileProtectedError",
    "ParseError",
    "MediaObject",
    "ModelApiConfig",
    "ParseConfig",
    "__version__",
    # 公共 API
    "parse_file",
    "Workbook",
    "Sheet",
    "Cell",
]

# 公共 API
from .engine import parse_file
from .ir.model import Cell, MediaObject, Sheet, Workbook
