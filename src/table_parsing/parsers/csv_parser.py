"""
CSV 格式解析器
"""

from pathlib import Path
from typing import Union

from .base import BaseParser


class CSVParser(BaseParser):
    """
    CSV 格式解析器

    解析 CSV 文件并转换为统一的中间表示
    """

    def parse(self, file_path: Union[str, Path]) -> None:
        """
        解析 CSV 文件

        Args:
            file_path: CSV 文件路径

        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 文件格式不正确
        """
        # 将在任务 6.1-6.4 中实现
        raise NotImplementedError("CSV parser will be implemented in tasks 6.1-6.4")
