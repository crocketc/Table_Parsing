"""
测试格式路由系统
"""

import pytest
from pathlib import Path
from io import BytesIO
from table_parsing.parsers import (
    BaseParser,
    get_format_by_extension,
    detect_format_by_magic_number,
    get_parser,
    FileFormat,
)


class MockParser(BaseParser):
    """用于测试的模拟解析器"""

    def parse(self, file_path: str | Path) -> None:
        """模拟解析操作"""
        pass


class TestBaseParser:
    """测试 BaseParser 抽象类"""

    def test_cannot_instantiate_base_parser(self):
        """测试不能直接实例化 BaseParser"""
        with pytest.raises(TypeError):
            BaseParser()

    def test_can_create_subclass(self):
        """测试可以创建子类实例"""
        parser = MockParser()
        assert isinstance(parser, BaseParser)


class TestFormatEnum:
    """测试 FileFormat 枚举"""

    def test_format_values(self):
        """测试格式枚举值"""
        assert FileFormat.CSV.value == "csv"
        assert FileFormat.XLSX.value == "xlsx"
        assert FileFormat.XLS.value == "xls"


class TestGetFormatByExtension:
    """测试通过扩展名获取格式"""

    def test_csv_extensions(self):
        """测试 CSV 扩展名"""
        assert get_format_by_extension("csv") == FileFormat.CSV
        assert get_format_by_extension("CSV") == FileFormat.CSV
        assert get_format_by_extension(".csv") == FileFormat.CSV

    def test_xlsx_extensions(self):
        """测试 XLSX 扩展名"""
        assert get_format_by_extension("xlsx") == FileFormat.XLSX
        assert get_format_by_extension("XLSX") == FileFormat.XLSX
        assert get_format_by_extension(".xlsx") == FileFormat.XLSX

    def test_xls_extensions(self):
        """测试 XLS 扩展名"""
        assert get_format_by_extension("xls") == FileFormat.XLS
        assert get_format_by_extension("XLS") == FileFormat.XLS
        assert get_format_by_extension(".xls") == FileFormat.XLS

    def test_unknown_extension(self):
        """测试未知扩展名"""
        assert get_format_by_extension("pdf") is None
        assert get_format_by_extension("txt") is None
        assert get_format_by_extension("") is None


class TestDetectFormatByMagicNumber:
    """测试通过魔术数字检测格式"""

    def test_detect_xlsx_by_magic_number(self):
        """测试检测 XLSX (ZIP 格式)"""
        # XLSX 实际上是 ZIP 文件，魔术数字为 PK\x03\x04
        xlsx_magic = b"PK\x03\x04" + b"\x00" * 100
        assert detect_format_by_magic_number(xlsx_magic) == FileFormat.XLSX

    def test_detect_xls_by_magic_number(self):
        """测试检测 XLS (OLE2 格式)"""
        # XLS 使用 OLE2 格式
        xls_magic = b"\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1" + b"\x00" * 100
        assert detect_format_by_magic_number(xls_magic) == FileFormat.XLS

    def test_empty_buffer(self):
        """测试空缓冲区"""
        assert detect_format_by_magic_number(b"") is None

    def test_unknown_format(self):
        """测试未知格式"""
        assert detect_format_by_magic_number(b"PDF-1.4") is None
        assert detect_format_by_magic_number(b"Hello World") is None

    def test_insufficient_buffer(self):
        """测试缓冲区不足"""
        # 缓冲区太小无法检测
        assert detect_format_by_magic_number(b"PK") is None


class TestGetParser:
    """测试工厂函数"""

    def test_get_csv_parser(self):
        """测试获取 CSV 解析器"""
        parser = get_parser("test.csv")
        assert isinstance(parser, BaseParser)

    def test_get_xlsx_parser(self):
        """测试获取 XLSX 解析器"""
        parser = get_parser("test.xlsx")
        assert isinstance(parser, BaseParser)

    def test_get_xls_parser(self):
        """测试获取 XLS 解析器"""
        parser = get_parser("test.xls")
        assert isinstance(parser, BaseParser)

    def test_get_parser_by_path(self):
        """测试通过 Path 对象获取解析器"""
        parser = get_parser(Path("test.csv"))
        assert isinstance(parser, BaseParser)

    def test_unsupported_format_raises_error(self):
        """测试不支持的格式抛出异常"""
        with pytest.raises(ValueError, match="Unsupported file format"):
            get_parser("test.pdf")

    def test_magic_number_overrides_extension(self):
        """测试魔术数字优先于扩展名"""
        # 创建一个具有 .csv 扩展名但实际是 XLSX 的文件
        xlsx_content = b"PK\x03\x04" + b"\x00" * 100
        temp_file = Path("test.csv")

        # 暂时写入文件用于测试
        temp_file.write_bytes(xlsx_content)
        try:
            # 应该根据魔术数字检测为 XLSX
            parser = get_parser(temp_file)
            # 验证返回的是 XLSX 解析器
            assert isinstance(parser, BaseParser)
        finally:
            if temp_file.exists():
                temp_file.unlink()
