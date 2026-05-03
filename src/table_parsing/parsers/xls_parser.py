"""
XLS 格式解析器
"""

import datetime as dt
from pathlib import Path
from typing import Union, Optional, Any, Literal

import xlrd

from ..ir.model import Workbook, Sheet, Cell
from .base import BaseParser


class XLSParser(BaseParser):
    """
    XLS 格式解析器

    解析 Excel 97-2003 (XLS) 文件并转换为统一的中间表示
    """

    # xlrd 单元格类型常量 (xlrd 2.0+)
    XL_CELL_TEXT = 1
    XL_CELL_NUMBER = 2
    XL_CELL_DATE = 3
    XL_CELL_BOOLEAN = 4
    XL_CELL_BLANK = 6

    def __init__(self) -> None:
        """初始化解析器"""
        self._workbook: Optional[Workbook] = None

    @staticmethod
    def _map_xlrd_type(xlrd_type: int) -> Literal["number", "string", "date", "bool", "blank"]:
        """
        将 xlrd 单元格类型映射到 IR data_type

        Args:
            xlrd_type: xlrd 单元格类型常量

        Returns:
            IR data_type 字符串
        """
        type_mapping: dict[int, Literal["number", "string", "date", "bool", "blank"]] = {
            XLSParser.XL_CELL_NUMBER: "number",
            XLSParser.XL_CELL_TEXT: "string",
            XLSParser.XL_CELL_DATE: "date",
            XLSParser.XL_CELL_BOOLEAN: "bool",
            XLSParser.XL_CELL_BLANK: "blank",
        }
        return type_mapping.get(xlrd_type, "string")  # type: ignore[return-value]

    def parse(self, file_path: Union[str, Path]) -> Workbook:
        """
        解析 XLS 文件

        Args:
            file_path: XLS 文件路径

        Returns:
            Workbook 对象

        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 文件格式不正确
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"XLS file not found: {file_path}")

        if not path.is_file():
            raise ValueError(f"Path is not a file: {file_path}")

        try:
            # 打开 XLS 工作簿
            # 注意：需要 formatting_info=True 来获取工作表可见性信息
            xl_workbook = xlrd.open_workbook(
                path,
                formatting_info=True,
                on_demand=False,
            )

            # 提取元数据
            metadata = self._extract_metadata(xl_workbook)

            # 解析所有工作表
            sheets = self._parse_sheets(xl_workbook)

            # 构建 Workbook 对象
            self._workbook = Workbook(metadata=metadata, sheets=sheets)

            return self._workbook

        except xlrd.XLRDError as e:
            raise ValueError(f"Invalid XLS file format: {e}") from e
        except Exception as e:
            raise ValueError(f"Error parsing XLS file: {e}") from e

    def _extract_metadata(self, xl_workbook: xlrd.Book) -> dict:
        """
        提取工作簿元数据

        Args:
            xl_workbook: xlrd Book 对象

        Returns:
            元数据字典
        """
        metadata = {}

        # 尝试提取作者信息
        if hasattr(xl_workbook, "user_name"):
            author = xl_workbook.user_name
            if author:
                metadata["author"] = author

        # 尝试提取创建时间
        if hasattr(xl_workbook, "creation_time"):
            creation_time = xl_workbook.creation_time
            if creation_time:
                # xlrd 返回的是 Unix 时间戳
                if isinstance(creation_time, (int, float)):
                    metadata["created"] = dt.datetime.fromtimestamp(creation_time).isoformat()

        # 尝试提取修改时间
        if hasattr(xl_workbook, "modification_time"):
            mod_time = xl_workbook.modification_time
            if mod_time:
                # xlrd 返回的是 Unix 时间戳
                if isinstance(mod_time, (int, float)):
                    metadata["modified"] = dt.datetime.fromtimestamp(mod_time).isoformat()

        # 添加其他可用的元数据
        if hasattr(xl_workbook, "codepage"):
            metadata["codepage"] = xl_workbook.codepage

        if hasattr(xl_workbook, "company"):
            company = xl_workbook.company
            if company:
                metadata["company"] = company

        return metadata

    def _parse_sheets(self, xl_workbook: xlrd.Book) -> list[Sheet]:
        """
        解析所有工作表

        Args:
            xl_workbook: xlrd Book 对象

        Returns:
            Sheet 对象列表
        """
        sheets = []

        for sheet_idx in range(xl_workbook.nsheets):
            xl_sheet = xl_workbook.sheet_by_index(sheet_idx)

            # 提取工作表信息
            sheet_name = xl_sheet.name
            # xlrd 2.0+ 不再支持工作表可见性检测，默认为 False
            # 如果需要隐藏工作表信息，需要使用 xlrd < 2.0 或其他库
            hidden = False
            max_row = xl_sheet.nrows
            max_col = xl_sheet.ncols

            # 解析单元格数据
            cells = self._parse_cells(xl_sheet)

            # 解析合并单元格
            self._apply_merged_cells(xl_sheet, cells)

            # 创建 Sheet 对象
            sheet = Sheet(
                name=sheet_name,
                hidden=hidden,
                max_row=max_row,
                max_col=max_col,
                cells=cells,
            )
            sheets.append(sheet)

        return sheets

    def _parse_cells(self, xl_sheet: xlrd.sheet.Sheet) -> list[list[Cell]]:
        """
        解析工作表的所有单元格

        Args:
            xl_sheet: xlrd Sheet 对象

        Returns:
            二维 Cell 对象列表
        """
        cells = []

        for row_idx in range(xl_sheet.nrows):
            row_cells = []
            for col_idx in range(xl_sheet.ncols):
                cell = self._parse_cell(xl_sheet, row_idx, col_idx)
                row_cells.append(cell)
            cells.append(row_cells)

        return cells

    def _parse_cell(self, xl_sheet: xlrd.sheet.Sheet, row_idx: int, col_idx: int) -> Cell:
        """
        解析单个单元格

        Args:
            xl_sheet: xlrd Sheet 对象
            row_idx: 行索引
            col_idx: 列索引

        Returns:
            Cell 对象
        """
        # 获取单元格类型和值
        xl_cell_type = xl_sheet.cell_type(row_idx, col_idx)
        xl_cell_value = xl_sheet.cell_value(row_idx, col_idx)

        # 映射到 IR data_type
        data_type = self._map_xlrd_type(xl_cell_type)

        # 转换单元格值
        value = self._convert_cell_value(xl_cell_value, xl_cell_type, xl_sheet, row_idx, col_idx)

        # 创建 Cell 对象
        return Cell(value=value, data_type=data_type)

    def _convert_cell_value(
        self,
        xl_value: Any,
        xl_type: int,
        xl_sheet: xlrd.sheet.Sheet,
        row_idx: int,
        col_idx: int
    ) -> Any:
        """
        转换单元格值到 IR 格式

        Args:
            xl_value: xlrd 单元格值
            xl_type: xlrd 单元格类型
            xl_sheet: xlrd Sheet 对象
            row_idx: 行索引
            col_idx: 列索引

        Returns:
            转换后的值
        """
        if xl_type == self.XL_CELL_BLANK:
            return None
        elif xl_type == self.XL_CELL_NUMBER:
            # 尝试转换为整数（如果是整数）
            if isinstance(xl_value, float) and xl_value.is_integer():
                return int(xl_value)
            return xl_value
        elif xl_type == self.XL_CELL_TEXT:
            return str(xl_value) if xl_value else ""
        elif xl_type == self.XL_CELL_BOOLEAN:
            return bool(xl_value)
        elif xl_type == self.XL_CELL_DATE:
            # xlrd 的日期类型需要特殊处理
            try:
                # 尝试作为日期时间处理
                datetuple = xlrd.xldate_as_tuple(xl_value, xl_sheet.book.datemode)
                if datetuple[3:6] == (0, 0, 0):
                    # 只有日期部分
                    return dt.date(*datetuple[:3])
                else:
                    # 包含时间部分
                    return dt.datetime(*datetuple)
            except:
                # 如果转换失败，返回原始值
                return xl_value
        else:
            return xl_value

    def _apply_merged_cells(self, xl_sheet: xlrd.sheet.Sheet, cells: list[list[Cell]]) -> None:
        """
        应用合并单元格信息

        Args:
            xl_sheet: xlrd Sheet 对象
            cells: 单元格矩阵（会原地修改）
        """
        # 获取合并单元格范围
        merged_ranges = xl_sheet.merged_cells

        for row0, row1, col0, col1 in merged_ranges:
            # row1 和 col1 是不包含的边界
            merge_range = self._format_merge_range(row0, col0, row1 - 1, col1 - 1)

            # 标记合并区域内的所有单元格
            for row_idx in range(row0, row1):
                for col_idx in range(col0, col1):
                    if row_idx < len(cells) and col_idx < len(cells[row_idx]):
                        cell = cells[row_idx][col_idx]
                        cell.is_merged = True
                        cell.merge_range = merge_range

    def _format_merge_range(self, row0: int, col0: int, row1: int, col1: int) -> str:
        """
        格式化合并单元格范围

        Args:
            row0: 起始行（0-based）
            col0: 起始列（0-based）
            row1: 结束行（0-based, 包含）
            col1: 结束列（0-based, 包含）

        Returns:
            范围字符串，如 "A1:C3"
        """
        def col_to_letter(col: int) -> str:
            """将列索引转换为字母（Excel 风格）"""
            result = ""
            while col >= 0:
                result = chr(col % 26 + ord('A')) + result
                col = col // 26 - 1
            return result

        start = f"{col_to_letter(col0)}{row0 + 1}"
        end = f"{col_to_letter(col1)}{row1 + 1}"

        if start == end:
            return start
        else:
            return f"{start}:{end}"
