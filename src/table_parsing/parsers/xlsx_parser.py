"""
XLSX 格式解析器
"""

from pathlib import Path
from typing import Union

from .base import BaseParser


class XLSXParser(BaseParser):
    """
    XLSX 格式解析器

    解析 Excel 2007+ (XLSX) 文件并转换为统一的中间表示
    """

    def parse(self, file_path: Union[str, Path]) -> None:
        """
        解析 XLSX 文件

        Args:
            file_path: XLSX 文件路径

        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 文件格式不正确
        """
        # 将在任务 8.1 中实现
        raise NotImplementedError("XLSX parser will be implemented in task 8.1")
