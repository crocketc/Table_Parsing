"""
Table Parsing IR 解析引擎

提供统一的 parse_file() 入口函数
"""

import logging
from pathlib import Path
from typing import Union

from .exceptions import TableParsingError
from .ir.model import Cell, Workbook
from .parsers.factory import get_parser

logger = logging.getLogger(__name__)


def parse_file(file_path: Union[str, Path]) -> Workbook:
    """
    解析表格文件并返回统一的中 IR 表示

    这是 Table Parsing IR 的主要入口函数。它负责：
    1. 验证文件存在性
    2. 自动检测文件格式
    3. 调用适当的解析器
    4. 返回标准化的 Workbook 对象

    Args:
        file_path: 表格文件路径，支持 CSV/XLS/XLSX 格式

    Returns:
        Workbook: 包含解析后数据的中间表示对象

    Raises:
        FileNotFoundError: 文件不存在
        ValueError: 文件路径无效或不支持的格式
        TableParsingError: 解析过程中的其他错误

    Examples:
        >>> from table_parsing import parse_file
        >>> workbook = parse_file("data.csv")
        >>> sheets = workbook.sheets
        >>> len(sheets)
        1

        >>> # 解析 XLSX 文件
        >>> workbook = parse_file("report.xlsx")
        >>> for sheet in workbook.sheets:
        ...     print(sheet.name)
    """
    path = Path(file_path)

    # 1. 文件存在性检查
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    if not path.is_file():
        raise ValueError(f"Path is not a file: {path}")

    # 2. 获取适当的解析器（工厂函数会自动检测格式）
    parser = get_parser(path)

    # 3. 调用解析器进行解析，返回 Workbook
    workbook = parser.parse(path)

    # 4. 确保返回 Workbook 对象
    if workbook is None:
        raise TableParsingError(f"Parser returned None for file: {path}")

    return workbook
