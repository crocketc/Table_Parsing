"""
解析器工厂函数
"""

from pathlib import Path
from typing import Union

from .base import BaseParser
from .registry import FileFormat, detect_format_by_magic_number, get_format_by_extension


def get_parser(file_path: Union[str, Path]) -> BaseParser:
    """
    根据文件路径获取适当的解析器实例

    检测逻辑：
    1. 如果文件存在，优先使用魔术数字检测格式
    2. 如果文件不存在或无法检测，使用扩展名推断
    3. 如果两种方法都无法确定，抛出 ValueError

    Args:
        file_path: 文件路径，可以是字符串或 Path 对象

    Returns:
        适当的解析器实例

    Raises:
        ValueError: 不支持的文件格式

    Examples:
        >>> parser = get_parser("data.csv")
        >>> isinstance(parser, CSVParser)
        True
        >>> parser = get_parser("data.xlsx")
        >>> isinstance(parser, XLSXParser)
        True
    """
    path = Path(file_path)
    extension = path.suffix.lstrip(".")

    # 首先尝试通过扩展名获取格式
    file_format = get_format_by_extension(extension)

    # 如果文件存在且可读，尝试通过魔术数字验证或修正格式
    if path.exists() and path.is_file():
        try:
            with open(path, "rb") as f:
                header = f.read(100)  # 读取前 100 字节用于魔术数字检测

            magic_format = detect_format_by_magic_number(header)

            # 如果魔术数字检测成功，使用检测结果
            if magic_format is not None:
                file_format = magic_format
        except (OSError, IOError):
            # 如果读取失败，继续使用扩展名推断
            pass

    # 根据格式返回相应的解析器
    if file_format == FileFormat.CSV:
        from .csv_parser import CSVParser

        return CSVParser()
    elif file_format == FileFormat.XLSX:
        from .xlsx_parser import XLSXParser

        return XLSXParser()
    elif file_format == FileFormat.XLS:
        from .xls_parser import XLSParser

        return XLSParser()
    else:
        raise ValueError(
            f"Unsupported file format: {extension}. "
            f"Supported formats: CSV, XLSX, XLS"
        )
