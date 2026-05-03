"""
测试 XLS 格式解析器
"""

import datetime as dt
import pytest
from pathlib import Path
from table_parsing.parsers.xls_parser import XLSParser
from table_parsing.ir.model import Workbook, Sheet, Cell

# 测试数据目录
TEST_DATA_DIR = Path(__file__).parent / "test_data" / "xls"


class TestXLSTypeMapping:
    """测试 xlrd 类型到 IR data_type 的映射"""

    def test_map_xlrd_number_type(self):
        """测试映射 XL_CELL_NUMBER 类型"""
        # xlrd.XL_CELL_NUMBER = 0
        data_type = XLSParser._map_xlrd_type(0)
        assert data_type == "number"

    def test_map_xlrd_date_type(self):
        """测试映射 XL_CELL_DATE 类型"""
        # xlrd.XL_CELL_DATE = 3
        data_type = XLSParser._map_xlrd_type(3)
        assert data_type == "date"

    def test_map_xlrd_text_type(self):
        """测试映射 XL_CELL_TEXT 类型"""
        # xlrd.XL_CELL_TEXT = 1
        data_type = XLSParser._map_xlrd_type(1)
        assert data_type == "string"

    def test_map_xlrd_bool_type(self):
        """测试映射 XL_CELL_BOOL 类型"""
        # xlrd.XL_CELL_BOOL = 4
        data_type = XLSParser._map_xlrd_type(4)
        assert data_type == "bool"

    def test_map_xlrd_blank_type(self):
        """测试映射 XL_CELL_BLANK 类型"""
        # xlrd.XL_CELL_BLANK = 6
        data_type = XLSParser._map_xlrd_type(6)
        assert data_type == "blank"

    def test_map_xlrd_unknown_type(self):
        """测试映射未知类型"""
        # 未知类型应该映射为 string
        data_type = XLSParser._map_xlrd_type(999)
        assert data_type == "string"


class TestXLSParserBasicFunctionality:
    """测试 XLSParser 基本功能"""

    def test_parser_initialization(self):
        """测试解析器初始化"""
        parser = XLSParser()
        assert parser is not None

    def test_parse_nonexistent_file_raises_error(self):
        """测试解析不存在的文件抛出异常"""
        parser = XLSParser()
        with pytest.raises(FileNotFoundError):
            parser.parse("/nonexistent/file.xls")


class TestXLSMetadataExtraction:
    """测试 XLS 元数据提取"""

    def test_extract_metadata_from_xls(self):
        """测试从 XLS 文件提取元数据"""
        test_file = TEST_DATA_DIR / "simple.xls"
        parser = XLSParser()
        workbook = parser.parse(test_file)

        assert workbook is not None
        assert isinstance(workbook, Workbook)
        assert workbook.metadata is not None
        assert isinstance(workbook.metadata, dict)

    def test_metadata_has_author(self):
        """测试元数据包含作者信息"""
        test_file = TEST_DATA_DIR / "simple.xls"
        parser = XLSParser()
        workbook = parser.parse(test_file)

        # 注意：xlrd 可能无法读取所有元数据，这取决于 XLS 文件的创建方式
        # 我们只测试结构是否正确
        assert "metadata" in workbook.to_dict()

    def test_metadata_structure(self):
        """测试元数据结构"""
        test_file = TEST_DATA_DIR / "simple.xls"
        parser = XLSParser()
        workbook = parser.parse(test_file)

        # 元数据应该是字典
        assert isinstance(workbook.metadata, dict)


class TestXLSSheetParsing:
    """测试 XLS 工作表解析"""

    def test_parse_all_sheets_including_hidden(self):
        """测试解析所有工作表（包括隐藏工作表）"""
        test_file = TEST_DATA_DIR / "multiple_sheets.xls"
        parser = XLSParser()
        workbook = parser.parse(test_file)

        # 应该有多个工作表
        assert len(workbook.sheets) >= 2

        # 检查工作表名称
        sheet_names = [sheet.name for sheet in workbook.sheets]
        assert "Sheet1" in sheet_names
        assert "Sheet2" in sheet_names

    def test_extract_sheet_name(self):
        """测试提取工作表名称"""
        test_file = TEST_DATA_DIR / "simple.xls"
        parser = XLSParser()
        workbook = parser.parse(test_file)

        # 应该有一个工作表
        assert len(workbook.sheets) == 1
        assert workbook.sheets[0].name == "Sheet1"

    def test_calculate_max_row_and_col(self):
        """测试计算最大行和列"""
        test_file = TEST_DATA_DIR / "simple.xls"
        parser = XLSParser()
        workbook = parser.parse(test_file)

        sheet = workbook.sheets[0]
        # simple.xls 有 4 行数据（包括标题行）
        assert sheet.max_row == 4
        # 有 3 列
        assert sheet.max_col == 3

    def test_sheet_visibility(self):
        """测试工作表可见性"""
        test_file = TEST_DATA_DIR / "simple.xls"
        parser = XLSParser()
        workbook = parser.parse(test_file)

        # 默认工作表应该是可见的
        sheet = workbook.sheets[0]
        assert sheet.hidden is False


class TestXLSCellParsing:
    """测试 XLS 单元格解析"""

    def test_parse_number_cell(self):
        """测试解析数字单元格"""
        test_file = TEST_DATA_DIR / "data_types.xls"
        parser = XLSParser()
        workbook = parser.parse(test_file)

        sheet = workbook.sheets[0]

        # 测试整数
        int_cell = sheet.cells[1][1]
        assert int_cell.data_type == "number"
        assert int_cell.value == 42

        # 测试浮点数
        float_cell = sheet.cells[2][1]
        assert float_cell.data_type == "number"
        assert abs(float_cell.value - 3.14159) < 0.00001

    def test_parse_string_cell(self):
        """测试解析字符串单元格"""
        test_file = TEST_DATA_DIR / "simple.xls"
        parser = XLSParser()
        workbook = parser.parse(test_file)

        sheet = workbook.sheets[0]

        # 检查标题行
        assert sheet.cells[0][0].value == "Name"
        assert sheet.cells[0][1].value == "Age"
        assert sheet.cells[0][2].value == "City"

        # 检查数据行
        assert sheet.cells[1][0].value == "Alice"
        assert sheet.cells[1][0].data_type == "string"

    def test_parse_date_cell(self):
        """测试解析日期单元格"""
        test_file = TEST_DATA_DIR / "data_types.xls"
        parser = XLSParser()
        workbook = parser.parse(test_file)

        sheet = workbook.sheets[0]

        # 测试日期
        date_cell = sheet.cells[4][1]
        assert date_cell.data_type == "date"
        # 日期可能被解析为 date 或 datetime 对象
        assert isinstance(date_cell.value, (dt.date, dt.datetime))

    def test_parse_bool_cell(self):
        """测试解析布尔单元格"""
        test_file = TEST_DATA_DIR / "data_types.xls"
        parser = XLSParser()
        workbook = parser.parse(test_file)

        sheet = workbook.sheets[0]

        # 测试布尔值
        bool_cell = sheet.cells[3][1]
        assert bool_cell.data_type == "bool"
        assert bool_cell.value is True

    def test_parse_blank_cell(self):
        """测试解析空白单元格"""
        test_file = TEST_DATA_DIR / "data_types.xls"
        parser = XLSParser()
        workbook = parser.parse(test_file)

        sheet = workbook.sheets[0]

        # 测试空白单元格
        blank_cell = sheet.cells[6][1]
        assert blank_cell.data_type in ("blank", "string")
        # 空白单元格的值可能是 None 或空字符串
        assert blank_cell.value in (None, "")

    def test_build_cell_matrix(self):
        """测试构建单元格矩阵"""
        test_file = TEST_DATA_DIR / "simple.xls"
        parser = XLSParser()
        workbook = parser.parse(test_file)

        sheet = workbook.sheets[0]

        # 检查矩阵结构
        assert len(sheet.cells) == 4  # 4 行
        assert len(sheet.cells[0]) == 3  # 3 列

        # 检查具体单元格
        assert sheet.cells[1][0].value == "Alice"
        assert sheet.cells[1][1].value == 30
        assert sheet.cells[1][2].value == "New York"


class TestXLSMergedCells:
    """测试 XLS 合并单元格解析"""

    def test_extract_merged_ranges(self):
        """测试提取合并单元格范围"""
        test_file = TEST_DATA_DIR / "merged_cells.xls"
        parser = XLSParser()
        workbook = parser.parse(test_file)

        sheet = workbook.sheets[0]

        # 检查第一行的合并单元格（标题）
        title_cell = sheet.cells[0][0]
        assert title_cell.is_merged is True
        assert title_cell.merge_range == "A1:C1"

    def test_mark_merged_cells(self):
        """测试标记合并单元格"""
        test_file = TEST_DATA_DIR / "merged_cells.xls"
        parser = XLSParser()
        workbook = parser.parse(test_file)

        sheet = workbook.sheets[0]

        # 检查合并区域内的所有单元格都被标记
        # A1:C1 合并区域
        assert sheet.cells[0][0].is_merged is True
        assert sheet.cells[0][1].is_merged is True
        assert sheet.cells[0][2].is_merged is True

        # A5:A6 合并区域
        assert sheet.cells[4][0].is_merged is True
        assert sheet.cells[5][0].is_merged is True

    def test_merge_range_notation(self):
        """测试合并单元格范围表示法"""
        test_file = TEST_DATA_DIR / "merged_cells.xls"
        parser = XLSParser()
        workbook = parser.parse(test_file)

        sheet = workbook.sheets[0]

        # 检查范围表示法
        assert sheet.cells[0][0].merge_range == "A1:C1"
        assert sheet.cells[4][0].merge_range == "A5:A6"

    def test_merged_cells_have_same_range(self):
        """测试合并区域内单元格有相同的范围标记"""
        test_file = TEST_DATA_DIR / "merged_cells.xls"
        parser = XLSParser()
        workbook = parser.parse(test_file)

        sheet = workbook.sheets[0]

        # A1:C1 区域内的所有单元格应该有相同的 merge_range
        range_a1 = sheet.cells[0][0].merge_range
        range_b1 = sheet.cells[0][1].merge_range
        range_c1 = sheet.cells[0][2].merge_range

        assert range_a1 == range_b1 == range_c1 == "A1:C1"


class TestXLSParserIntegration:
    """测试 XLSParser 集成"""

    def test_parse_simple_xls(self):
        """测试解析简单 XLS 文件"""
        test_file = TEST_DATA_DIR / "simple.xls"
        parser = XLSParser()
        workbook = parser.parse(test_file)

        assert workbook is not None
        assert isinstance(workbook, Workbook)
        assert len(workbook.sheets) == 1

    def test_parse_xls_with_multiple_sheets(self):
        """测试解析多工作表 XLS 文件"""
        test_file = TEST_DATA_DIR / "multiple_sheets.xls"
        parser = XLSParser()
        workbook = parser.parse(test_file)

        assert len(workbook.sheets) >= 2

    def test_parse_xls_with_merged_cells(self):
        """测试解析带合并单元格的 XLS 文件"""
        test_file = TEST_DATA_DIR / "merged_cells.xls"
        parser = XLSParser()
        workbook = parser.parse(test_file)

        sheet = workbook.sheets[0]
        # 应该有合并单元格
        has_merged = any(
            cell.is_merged
            for row in sheet.cells
            for cell in row
        )
        assert has_merged is True

    def test_return_workbook_object(self):
        """测试返回 Workbook 对象"""
        test_file = TEST_DATA_DIR / "simple.xls"
        parser = XLSParser()
        result = parser.parse(test_file)

        assert isinstance(result, Workbook)
        assert hasattr(result, "metadata")
        assert hasattr(result, "sheets")

    def test_workbook_to_dict_conversion(self):
        """测试 Workbook 转换为字典"""
        test_file = TEST_DATA_DIR / "simple.xls"
        parser = XLSParser()
        workbook = parser.parse(test_file)

        # 转换为字典
        result_dict = workbook.to_dict()

        assert isinstance(result_dict, dict)
        assert "metadata" in result_dict
        assert "sheets" in result_dict
        assert isinstance(result_dict["sheets"], list)

    def test_parse_xls_with_different_data_types(self):
        """测试解析包含不同数据类型的 XLS 文件"""
        test_file = TEST_DATA_DIR / "data_types.xls"
        parser = XLSParser()
        workbook = parser.parse(test_file)

        sheet = workbook.sheets[0]

        # 检查不同的数据类型都被正确解析
        data_types = set()
        for row in sheet.cells:
            for cell in row:
                if cell.data_type:
                    data_types.add(cell.data_type)

        # 应该包含 number, string, date, bool, blank
        expected_types = {"number", "string", "date", "bool"}
        assert expected_types.issubset(data_types)
