"""
基础解析器抽象类
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Union

from ..ir.model import Workbook


class BaseParser(ABC):
    """
    所有表格解析器的抽象基类

    定义了所有解析器必须实现的接口
    """

    @abstractmethod
    def parse(self, file_path: Union[str, Path]) -> Workbook:
        """
        解析表格文件

        Args:
            file_path: 文件路径，可以是字符串或 Path 对象

        Returns:
            Workbook: 解析后的工作簿对象

        Raises:
            FileNotFoundError: 文件不存在
            PermissionError: 没有读取权限
            ValueError: 文件格式不正确或损坏
        """
        pass
