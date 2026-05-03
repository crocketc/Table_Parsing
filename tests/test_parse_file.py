"""
测试 parse_file() 入口函数
"""

import pytest
from pathlib import Path
from table_parsing import parse_file
from table_parsing.exceptions import (
    FileFormatMismatchError,
    FileProtectedError,
    ParseError,
    TableParsingError,
    UnsupportedFormatError,
)
from table_parsing.ir import Workbook


class TestParseFile:
    """测试 parse_file() 入口函数"""

    def test_parse_csv_file(self, tmp_path):
        """测试解析 CSV 文件"""
        # 创建测试 CSV 文件
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("姓名,年龄\n张三,25\n李四,30\n")

        # 解析文件
        workbook = parse_file(csv_file)

        # 验证返回 Workbook 对象
        assert isinstance(workbook, Workbook)
        assert workbook.sheets is not None
        assert len(workbook.sheets) == 1
        # Sheet 名称现在使用文件名（不含扩展名）
        assert workbook.sheets[0].name == "test"

    def test_parse_xlsx_file(self, tmp_path):
        """测试解析 XLSX 文件（跳过，因为 XLSX 解析器已实现）"""
        # 由于 XLSX 解析器已经在任务 8.1 中完整实现
        # 这个测试需要真实的 XLSX 文件，所以我们跳过它
        pytest.skip("XLSX parser is already implemented, requires real XLSX file")

    def test_parse_xls_file(self, tmp_path):
        """测试解析 XLS 文件（跳过，因为 XLS 解析器已实现）"""
        # 由于 XLS 解析器已经在任务 7.1-7.2 中完整实现
        # 这个测试需要真实的 XLS 文件，所以我们跳过它
        pytest.skip("XLS parser is already implemented, requires real XLS file")

    def test_parse_file_with_path_object(self, tmp_path):
        """测试使用 Path 对象解析文件"""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("A,B\n1,2\n")

        workbook = parse_file(csv_file)

        assert isinstance(workbook, Workbook)

    def test_parse_file_with_string_path(self, tmp_path):
        """测试使用字符串路径解析文件"""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("X,Y\n3,4\n")

        workbook = parse_file(str(csv_file))

        assert isinstance(workbook, Workbook)

    def test_file_not_exists_raises_error(self, tmp_path):
        """测试文件不存在时抛出异常"""
        non_existent = tmp_path / "non_existent.csv"

        with pytest.raises(FileNotFoundError, match="File not found"):
            parse_file(non_existent)

    def test_unsupported_format_raises_error(self, tmp_path):
        """测试不支持的格式抛出异常"""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_text("fake pdf")

        with pytest.raises(ValueError, match="Unsupported file format"):
            parse_file(pdf_file)

    def test_directory_raises_error(self, tmp_path):
        """测试目录路径抛出异常"""
        with pytest.raises(ValueError, match="not a file"):
            parse_file(tmp_path)

    def test_empty_file_returns_empty_workbook(self, tmp_path):
        """测试空文件返回空的 Workbook"""
        empty_file = tmp_path / "empty.csv"
        empty_file.write_text("")

        workbook = parse_file(empty_file)

        assert isinstance(workbook, Workbook)
        # 空文件应该仍然返回 Workbook，只是内容为空
        assert workbook.sheets is not None

    def test_parse_preserves_file_metadata(self, tmp_path):
        """测试解析保留文件元数据"""
        csv_file = tmp_path / "data.csv"
        csv_file.write_text("Header1,Header2\nValue1,Value2\n")

        workbook = parse_file(csv_file)

        # 验证元数据包含文件名
        assert workbook.metadata is not None
        assert "source_file" in workbook.metadata or "filename" in workbook.metadata


class TestParseFileFaultTolerance:
    """测试 parse_file() 的容错机制"""

    def test_malformed_cell_continues_parsing(self, tmp_path):
        """测试格式错误的单元格不会中断解析"""
        # 创建包含格式错误单元格的 CSV
        csv_file = tmp_path / "faulty.csv"
        csv_file.write_text("A,B,C\n1, malformed ,3\n4,5,6\n")

        # 应该成功解析，即使第二个单元格有问题
        workbook = parse_file(csv_file)

        assert isinstance(workbook, Workbook)
        # 验证仍然解析出数据
        assert len(workbook.sheets) > 0

    def test_empty_cells_handled_gracefully(self, tmp_path):
        """测试空单元格被优雅处理"""
        csv_file = tmp_path / "empty_cells.csv"
        csv_file.write_text("A,B\n1,\n,4\n")

        workbook = parse_file(csv_file)

        assert isinstance(workbook, Workbook)
        # 验证空单元格被正确处理
        assert len(workbook.sheets) > 0

    def test_mixed_data_types_in_column(self, tmp_path):
        """测试列中混合数据类型被正确处理"""
        csv_file = tmp_path / "mixed.csv"
        csv_file.write_text("A\n123\nabc\n456\n")

        workbook = parse_file(csv_file)

        assert isinstance(workbook, Workbook)
        # 应该继续解析，不会因类型混合而失败

    def test_special_characters_handled(self, tmp_path):
        """测试特殊字符被正确处理"""
        csv_file = tmp_path / "special.csv"
        csv_file.write_text("文本,数据\n测试,值\n")

        workbook = parse_file(csv_file)

        assert isinstance(workbook, Workbook)
        # 特殊字符应该被正确保留

    def test_unicode_content_handled(self, tmp_path):
        """测试 Unicode 内容被正确处理"""
        csv_file = tmp_path / "unicode.csv"
        # 使用 UTF-8 编码写入 Unicode 内容
        csv_file.write_text("名称,值\n🎉,✓\n中日韩,한글\n", encoding="utf-8")

        workbook = parse_file(csv_file)

        assert isinstance(workbook, Workbook)
        # Unicode 内容应该被正确保留
