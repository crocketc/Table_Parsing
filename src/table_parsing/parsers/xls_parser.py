"""
XLS 格式解析器
"""

from pathlib import Path
from typing import Union

from .base import BaseParser


class XLSParser(BaseParser):
    """
    XLS 格式解析器

    解析 Excel 97-2003 (XLS) 文件并转换为统一的中间表示
    """

    def parse(self, file_path: Union[str, Path]) -> None:
        """
        解析 XLS 文件

        Args:
            file_path: XLS 文件路径

        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 文件格式不正确
        """
        # 将在任务 7.1-7.2 中实现
        raise NotImplementedError("XLS parser will be implemented in tasks 7.1-7.2")
