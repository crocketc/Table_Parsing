"""
格式注册表和魔术数字检测
"""

from enum import Enum
from typing import Optional


class FileFormat(Enum):
    """
    支持的文件格式枚举

    Attributes:
        CSV: CSV 格式
        XLSX: Excel 2007+ 格式 (Office Open XML)
        XLS: Excel 97-2003 格式 (OLE2)
    """

    CSV = "csv"
    XLSX = "xlsx"
    XLS = "xls"


# 扩展名到格式的映射
EXTENSION_MAP = {
    "csv": FileFormat.CSV,
    "xlsx": FileFormat.XLSX,
    "xls": FileFormat.XLS,
}

# 魔术数字定义
MAGIC_NUMBERS = {
    FileFormat.XLSX: b"PK\x03\x04",  # ZIP 文件头（XLSX 是 ZIP 格式）
    FileFormat.XLS: b"\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1",  # OLE2 文件头
}


def get_format_by_extension(extension: str) -> Optional[FileFormat]:
    """
    通过文件扩展名获取格式

    Args:
        extension: 文件扩展名，带或不带点号，大小写不敏感

    Returns:
        FileFormat 枚举值，如果不支持则返回 None

    Examples:
        >>> get_format_by_extension("csv")
        <FileFormat.CSV: 'csv'>
        >>> get_format_by_extension(".xlsx")
        <FileFormat.XLSX: 'xlsx'>
        >>> get_format_by_extension("pdf")
        None
    """
    # 移除前导点号
    ext = extension.lower().lstrip(".")

    return EXTENSION_MAP.get(ext)


def detect_format_by_magic_number(data: bytes) -> Optional[FileFormat]:
    """
    通过魔术数字检测文件格式

    Args:
        data: 文件前几个字节的字节串

    Returns:
        FileFormat 枚举值，如果无法识别则返回 None

    Examples:
        >>> detect_format_by_magic_number(b"PK\\x03\\x04...")
        <FileFormat.XLSX: 'xlsx'>
        >>> detect_format_by_magic_number(b"\\xD0\\xCF\\x11\\xE0...")
        <FileFormat.XLS: 'xls'>
    """
    if not data or len(data) < 8:
        return None

    for format_type, magic in MAGIC_NUMBERS.items():
        if data.startswith(magic):
            return format_type

    return None
