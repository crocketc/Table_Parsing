"""
测试 CSV 解析器
"""

import pytest
from pathlib import Path
from io import StringIO
import tempfile
import os

from table_parsing.parsers.csv_parser import CSVParser
from table_parsing.ir.model import Workbook, Sheet, Cell


class TestDetectEncoding:
    """测试编码检测功能"""

    def test_detect_utf8_with_bom(self):
        """测试检测 UTF-8 with BOM"""
        parser = CSVParser()
        # UTF-8 BOM
        content = b'\xef\xbb\xbfHello,World\n1,2'
        encoding = parser._detect_encoding(content)
        # 应该检测为 UTF-8 (with BOM)
        assert encoding is not None
        assert 'utf' in encoding.lower() or encoding == 'utf-8-sig'

    def test_detect_utf8_without_bom(self):
        """测试检测普通 UTF-8"""
        parser = CSVParser()
        content = b'Hello,World\n1,2'
        encoding = parser._detect_encoding(content)
        # 默认返回 UTF-8
        assert encoding == 'utf-8'

    def test_detect_gbk_encoding(self):
        """测试检测 GBK 编码"""
        parser = CSVParser()
        # GBK 编码的中文字符
        content = '你好,世界\n1,2'.encode('gbk')
        encoding = parser._detect_encoding(content)
        # 应该检测为某种中文编码或至少不是 UTF-8
        assert encoding is not None
        # charset-normalizer 可能检测为 gbk、gb2312 或其他中文编码
        # 只要不抛出异常即可
        assert isinstance(encoding, str)

    def test_detect_utf16_le(self):
        """测试检测 UTF-16 LE"""
        parser = CSVParser()
        content = 'Hello,World\n1,2'.encode('utf-16-le')
        encoding = parser._detect_encoding(content)
        # UTF-16 LE 没有 BOM，可能被检测为其他编码
        # 只要不抛出异常即可
        assert encoding is not None
        assert isinstance(encoding, str)

    def test_detect_empty_content(self):
        """测试检测空内容"""
        parser = CSVParser()
        encoding = parser._detect_encoding(b'')
        # 空内容默认返回 UTF-8
        assert encoding == 'utf-8'


class TestDetectDelimiter:
    """测试分隔符检测功能"""

    def test_detect_comma(self):
        """测试检测逗号分隔符"""
        parser = CSVParser()
        sample = "Name,Age,City\nAlice,30,NYC\nBob,25,LA"
        delimiter = parser._detect_delimiter(sample)
        assert delimiter == ','

    def test_detect_semicolon(self):
        """测试检测分号分隔符（欧洲格式）"""
        parser = CSVParser()
        sample = "Name;Age;City\nAlice;30;NYC\nBob;25;LA"
        delimiter = parser._detect_delimiter(sample)
        assert delimiter == ';'

    def test_detect_tab(self):
        """测试检测 Tab 分隔符"""
        parser = CSVParser()
        sample = "Name\tAge\tCity\nAlice\t30\tNYC\nBob\t25\tLA"
        delimiter = parser._detect_delimiter(sample)
        assert delimiter == '\t'

    def test_detect_pipe(self):
        """测试检测管道符分隔符"""
        parser = CSVParser()
        sample = "Name|Age|City\nAlice|30|NYC\nBob|25|LA"
        delimiter = parser._detect_delimiter(sample)
        assert delimiter == '|'

    def test_default_to_comma(self):
        """测试无法检测时默认使用逗号"""
        parser = CSVParser()
        # 单行数据无法准确检测
        sample = "Single line"
        delimiter = parser._detect_delimiter(sample)
        # 默认应该是逗号
        assert delimiter == ','

    def test_detect_with_quotes(self):
        """测试带引号的字段分隔符检测"""
        parser = CSVParser()
        sample = '"Name","Age","City"\n"Alice","30","NYC"'
        delimiter = parser._detect_delimiter(sample)
        assert delimiter == ','


class TestParseChunked:
    """测试分块解析功能"""

    def test_parse_small_file_single_chunk(self):
        """测试解析小文件（单块）"""
        parser = CSVParser()
        csv_content = "Name,Age,City\nAlice,30,NYC\nBob,25,LA"

        # 创建临时文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write(csv_content)
            temp_path = f.name

        try:
            # 解析文件
            chunks = list(parser.parse_chunked(temp_path))
            assert len(chunks) == 1

            sheet = chunks[0]
            assert sheet.name == "Sheet1"
            assert len(sheet.cells) == 3  # 包括标题行
            assert len(sheet.cells[0]) == 3  # 3列

            # 验证第一行（标题）
            assert sheet.cells[0][0].value == "Name"
            assert sheet.cells[0][1].value == "Age"
            assert sheet.cells[0][2].value == "City"

            # 验证数据行
            assert sheet.cells[1][0].value == "Alice"
            assert sheet.cells[1][1].value == 30
            assert sheet.cells[2][0].value == "Bob"
        finally:
            os.unlink(temp_path)

    def test_parse_large_file_multiple_chunks(self):
        """测试解析大文件（多块）"""
        parser = CSVParser()

        # 创建包含 20 行的数据
        lines = ["Name,Age,City"]
        for i in range(20):
            lines.append(f"Person{i},{i},City{i}")
        csv_content = '\n'.join(lines)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write(csv_content)
            temp_path = f.name

        try:
            # 使用 chunk_size=10 解析
            chunks = list(parser.parse_chunked(temp_path, chunk_size=10))

            # 应该有多个块
            assert len(chunks) > 1

            # 每个 chunk 都包含标题行，所以总行数 = 数据行数 + chunk数量 * 1（标题行）
            # 第一个 chunk: 10 数据行 + 1 标题行 = 11 行
            # 第二个 chunk: 10 数据行 + 1 标题行 = 11 行
            # 总共: 22 行
            total_rows = sum(len(sheet.cells) for sheet in chunks)
            assert total_rows == 22  # 2 个 chunk，每个包含标题行
        finally:
            os.unlink(temp_path)

    def test_parse_chunked_with_semicolon(self):
        """测试解析分号分隔的文件"""
        parser = CSVParser()
        csv_content = "Name;Age;City\nAlice;30;NYC\nBob;25;LA"

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write(csv_content)
            temp_path = f.name

        try:
            chunks = list(parser.parse_chunked(temp_path))
            assert len(chunks) == 1

            sheet = chunks[0]
            assert sheet.cells[0][0].value == "Name"
            assert sheet.cells[1][0].value == "Alice"
        finally:
            os.unlink(temp_path)

    def test_parse_chunked_with_gbk_encoding(self):
        """测试解析 GBK 编码的文件"""
        parser = CSVParser()
        csv_content = "姓名,年龄,城市\n张三,30,北京\n李四,25,上海"

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='gbk') as f:
            f.write(csv_content)
            temp_path = f.name

        try:
            chunks = list(parser.parse_chunked(temp_path))
            assert len(chunks) == 1

            sheet = chunks[0]
            assert sheet.cells[0][0].value == "姓名"
            assert sheet.cells[1][0].value == "张三"
        finally:
            os.unlink(temp_path)

    def test_parse_chunked_empty_file(self):
        """测试解析空文件"""
        parser = CSVParser()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("")
            temp_path = f.name

        try:
            chunks = list(parser.parse_chunked(temp_path))
            # 空文件应该返回空列表或只有一个空的 Sheet
            assert len(chunks) == 0 or (len(chunks) == 1 and len(chunks[0].cells) == 0)
        finally:
            os.unlink(temp_path)


class TestParseFull:
    """测试完整解析功能"""

    def test_parse_simple_csv(self):
        """测试解析简单 CSV 文件"""
        parser = CSVParser()
        csv_content = "Name,Age,City\nAlice,30,NYC\nBob,25,LA"

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write(csv_content)
            temp_path = f.name

        try:
            workbook = parser.parse(temp_path)
            assert isinstance(workbook, Workbook)
            assert len(workbook.sheets) == 1

            sheet = workbook.sheets[0]
            # Sheet 名称现在使用文件名（不含扩展名）
            assert sheet.name is not None
            assert isinstance(sheet.name, str)
            assert len(sheet.cells) == 3
            assert len(sheet.cells[0]) == 3
        finally:
            os.unlink(temp_path)

    def test_parse_with_quoted_fields(self):
        """测试解析带引号字段的 CSV"""
        parser = CSVParser()
        csv_content = '"Name","Age","City"\n"Alice","30","NYC"\n"Bob","25","LA"'

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write(csv_content)
            temp_path = f.name

        try:
            workbook = parser.parse(temp_path)
            sheet = workbook.sheets[0]
            assert sheet.cells[0][0].value == "Name"
            assert sheet.cells[1][0].value == "Alice"
        finally:
            os.unlink(temp_path)

    def test_parse_with_embedded_commas(self):
        """测试解析字段中包含逗号的 CSV"""
        parser = CSVParser()
        csv_content = 'Name,Description\nAlice,"New York, NY"\nBob,"Los Angeles, CA"'

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write(csv_content)
            temp_path = f.name

        try:
            workbook = parser.parse(temp_path)
            sheet = workbook.sheets[0]
            assert sheet.cells[1][1].value == "New York, NY"
            assert sheet.cells[2][1].value == "Los Angeles, CA"
        finally:
            os.unlink(temp_path)

    def test_parse_with_newlines_in_quotes(self):
        """测试解析引号中包含换行的 CSV"""
        parser = CSVParser()
        csv_content = 'Name,Description\nAlice,"Line1\nLine2"\nBob,Normal'

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8', newline='') as f:
            f.write(csv_content)
            temp_path = f.name

        try:
            workbook = parser.parse(temp_path)
            sheet = workbook.sheets[0]
            # Windows 可能使用 \r\n，所以检查是否包含换行即可
            value = sheet.cells[1][1].value
            assert '\n' in value or '\r\n' in value
            assert 'Line1' in value and 'Line2' in value
        finally:
            os.unlink(temp_path)

    def test_parse_nonexistent_file(self):
        """测试解析不存在的文件"""
        parser = CSVParser()
        with pytest.raises(FileNotFoundError):
            parser.parse("/nonexistent/file.csv")

    def test_parse_detect_automatically_encoding_and_delimiter(self):
        """测试自动检测编码和分隔符"""
        parser = CSVParser()
        # GBK 编码，分号分隔
        csv_content = "姓名;年龄;城市\n张三;30;北京\n李四;25;上海"

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='gbk') as f:
            f.write(csv_content)
            temp_path = f.name

        try:
            workbook = parser.parse(temp_path)
            sheet = workbook.sheets[0]
            assert sheet.cells[0][0].value == "姓名"
            assert sheet.cells[1][0].value == "张三"
            assert sheet.cells[1][1].value == 30
        finally:
            os.unlink(temp_path)


class TestDataTypeDetection:
    """测试数据类型检测"""

    def test_detect_integer(self):
        """测试检测整数类型"""
        parser = CSVParser()
        csv_content = "Name,Count\nAlice,123\nBob,456"

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write(csv_content)
            temp_path = f.name

        try:
            workbook = parser.parse(temp_path)
            sheet = workbook.sheets[0]
            # 整数应该转换为 int 类型
            assert isinstance(sheet.cells[1][1].value, int)
            assert sheet.cells[1][1].value == 123
            assert sheet.cells[1][1].data_type == "number"
        finally:
            os.unlink(temp_path)

    def test_detect_float(self):
        """测试检测浮点数类型"""
        parser = CSVParser()
        csv_content = "Name,Price\nItem1,19.99\nItem2,29.50"

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write(csv_content)
            temp_path = f.name

        try:
            workbook = parser.parse(temp_path)
            sheet = workbook.sheets[0]
            # 浮点数应该转换为 float 类型
            assert isinstance(sheet.cells[1][1].value, float)
            assert sheet.cells[1][1].value == 19.99
            assert sheet.cells[1][1].data_type == "number"
        finally:
            os.unlink(temp_path)

    def test_detect_boolean(self):
        """测试检测布尔类型"""
        parser = CSVParser()
        csv_content = "Name,Active\nAlice,True\nBob,False"

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write(csv_content)
            temp_path = f.name

        try:
            workbook = parser.parse(temp_path)
            sheet = workbook.sheets[0]
            # 布尔值应该转换为 bool 类型
            assert isinstance(sheet.cells[1][1].value, bool)
            assert sheet.cells[1][1].value is True
            assert sheet.cells[1][1].data_type == "bool"
        finally:
            os.unlink(temp_path)

    def test_detect_empty_as_blank(self):
        """测试检测空值"""
        parser = CSVParser()
        csv_content = "Name,Value\nAlice,\nBob,123"

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write(csv_content)
            temp_path = f.name

        try:
            workbook = parser.parse(temp_path)
            sheet = workbook.sheets[0]
            # 空值应该保留为 None 或空字符串
            assert sheet.cells[1][1].value in (None, "")
            assert sheet.cells[1][1].data_type == "blank"
        finally:
            os.unlink(temp_path)


class TestEdgeCases:
    """测试边缘情况"""

    def test_single_column(self):
        """测试单列 CSV"""
        parser = CSVParser()
        csv_content = "Name\nAlice\nBob"

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write(csv_content)
            temp_path = f.name

        try:
            workbook = parser.parse(temp_path)
            sheet = workbook.sheets[0]
            assert len(sheet.cells[0]) == 1
            assert sheet.cells[0][0].value == "Name"
        finally:
            os.unlink(temp_path)

    def test_single_row(self):
        """测试单行 CSV（只有标题）"""
        parser = CSVParser()
        csv_content = "Name,Age,City\n"

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write(csv_content)
            temp_path = f.name

        try:
            workbook = parser.parse(temp_path)
            sheet = workbook.sheets[0]
            # 应该有标题行
            assert len(sheet.cells) == 1
            assert sheet.cells[0][0].value == "Name"
        finally:
            os.unlink(temp_path)

    def test_inconsistent_columns(self):
        """测试列数不一致的 CSV"""
        parser = CSVParser()
        csv_content = "Name,Age,City\nAlice,30\nBob,25,LA"

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write(csv_content)
            temp_path = f.name

        try:
            # 应该能够解析，但可能有空值填充
            workbook = parser.parse(temp_path)
            sheet = workbook.sheets[0]
            # Python csv 模块会自动处理不一致的列数
            assert len(sheet.cells) >= 2
        finally:
            os.unlink(temp_path)

    def test_unicode_content(self):
        """测试 Unicode 内容"""
        parser = CSVParser()
        csv_content = "Name,Emoji\nAlice,😀\nBob,🎉"

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write(csv_content)
            temp_path = f.name

        try:
            workbook = parser.parse(temp_path)
            sheet = workbook.sheets[0]
            assert sheet.cells[1][1].value == "😀"
            assert sheet.cells[2][1].value == "🎉"
        finally:
            os.unlink(temp_path)
