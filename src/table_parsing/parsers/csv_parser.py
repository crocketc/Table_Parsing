"""
CSV 格式解析器
"""

import csv
import logging
from pathlib import Path
from typing import Union

from ..ir.model import Cell, Sheet, Workbook
from .base import BaseParser

logger = logging.getLogger(__name__)


class CSVParser(BaseParser):
    """
    CSV 格式解析器

    解析 CSV 文件并转换为统一的中间表示
    """

    def parse(self, file_path: Union[str, Path]) -> Workbook:
        """
        解析 CSV 文件

        Args:
            file_path: CSV 文件路径

        Returns:
            Workbook: 包含解析后数据的工作簿对象

        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 文件格式不正确
        """
        path = Path(file_path)

        # 读取 CSV 文件
        cells = []
        max_row = 0
        max_col = 0

        # 尝试多种编码
        encodings = ["utf-8", "gbk", "gb2312", "utf-16", "latin1"]
        f = None
        content = None
        used_encoding = None

        for encoding in encodings:
            try:
                f = open(path, "r", encoding=encoding, newline="")
                content = f.read(1024)
                f.seek(0)
                used_encoding = encoding
                break
            except UnicodeDecodeError:
                if f:
                    f.close()
                continue

        if f is None:
            raise ValueError(f"Could not decode file with any of these encodings: {encodings}")

        try:
            # 使用 csv.Sniffer 检测分隔符
            try:
                dialect = csv.Sniffer().sniff(content, delimiters=",;\t")
                f.seek(0)
                reader = csv.reader(f, dialect)
            except csv.Error:
                # 如果检测失败，默认使用逗号分隔符
                f.seek(0)
                reader = csv.reader(f)

            for row_idx, row in enumerate(reader):
                cell_row = []
                for col_idx, value in enumerate(row):
                    # 使用 try/except 包裹每个单元格的创建
                    try:
                        cell = self._parse_cell(value, row_idx, col_idx)
                        cell_row.append(cell)
                    except Exception as e:
                        # 单元格级别的容错：记录警告并返回空 Cell
                        logger.warning(
                            f"Failed to parse cell at ({row_idx}, {col_idx}): {e}. "
                            f"Using empty cell instead."
                        )
                        # 返回空的 Cell 对象
                        cell_row.append(Cell(value=None, data_type="blank"))

                cells.append(cell_row)
                max_row = row_idx + 1
                if len(row) > max_col:
                    max_col = len(row)

        except Exception as e:
            logger.error(f"Failed to parse CSV file {path}: {e}")
            raise
        finally:
            if f:
                f.close()

        # 创建 Sheet
        sheet = Sheet(
            name=path.name,
            hidden=False,
            max_row=max_row,
            max_col=max_col,
            cells=cells,
        )

        # 创建 Workbook
        workbook = Workbook(
            metadata={
                "source_file": str(path),
                "format": "csv",
                "encoding": used_encoding,
            },
            sheets=[sheet],
        )

        return workbook

    def _parse_cell(self, value: str, row_idx: int, col_idx: int) -> Cell:
        """
        解析单个单元格的值

        Args:
            value: 单元格的字符串值
            row_idx: 行索引
            col_idx: 列索引

        Returns:
            Cell: 解析后的单元格对象
        """
        # 尝试解析为数字
        try:
            # 尝试解析为整数
            if "." not in value and "e" not in value.lower():
                return Cell(value=int(value), data_type="number", raw_value=value)
            else:
                # 尝试解析为浮点数
                return Cell(value=float(value), data_type="number", raw_value=value)
        except ValueError:
            pass

        # 尝试解析为布尔值
        if value.lower() in ("true", "false"):
            return Cell(
                value=value.lower() == "true",
                data_type="bool",
                raw_value=value,
            )

        # 空值
        if not value or value.strip() == "":
            return Cell(value=None, data_type="blank", raw_value=value)

        # 默认为字符串
        return Cell(value=value, data_type="string", raw_value=value)
