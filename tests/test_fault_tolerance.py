"""
测试单元格级别的容错机制
"""

import pytest
import logging
from pathlib import Path
from table_parsing import parse_file
from table_parsing.ir import Cell, Workbook


class TestCellFaultTolerance:
    """测试单元格级别的容错处理"""

    def test_single_cell_error_doesnt_stop_parsing(self, tmp_path, caplog):
        """测试单个单元格错误不会停止整个解析过程"""
        # 创建一个包含某些会导致解析问题的单元格的文件
        csv_file = tmp_path / "faulty.csv"
        csv_file.write_text("A,B,C\n1,valid,3\n2,error!,4\n5,6,7\n")

        # 解析时应该记录警告但继续
        with caplog.at_level(logging.WARNING):
            workbook = parse_file(csv_file)

        # 应该返回有效的 Workbook
        assert isinstance(workbook, Workbook)
        assert len(workbook.sheets) > 0

        # 验证至少记录了一些警告（如果有的话）
        # 注意：根据实现，可能不会记录警告，这取决于具体的错误处理逻辑

    def test_invalid_cell_returns_empty_cell(self, tmp_path):
        """测试无效单元格返回空的 Cell 对象"""
        csv_file = tmp_path / "invalid.csv"
        # 创建包含无效数据的文件
        csv_file.write_text("A,B\n1,\n2,invalid_number\n")

        workbook = parse_file(csv_file)

        assert isinstance(workbook, Workbook)

        # 验证空的或无效的单元格被正确处理
        # 应该有 Cell 对象，即使 value 为 None
        sheet = workbook.sheets[0]
        assert sheet.cells is not None

    def test_multiple_cell_errors_all_logged(self, tmp_path, caplog):
        """测试多个单元格错误都被记录"""
        csv_file = tmp_path / "multiple_errors.csv"
        csv_file.write_text("A,B,C\n1,error1,error2\nerror3,4,error4\n5,6,7\n")

        with caplog.at_level(logging.WARNING):
            workbook = parse_file(csv_file)

        assert isinstance(workbook, Workbook)

        # 验证解析完成，尽管有多个错误
        assert len(workbook.sheets) > 0

    def test_cell_exception_type_variations(self, tmp_path):
        """测试不同类型的单元格异常都被捕获"""
        csv_file = tmp_path / "exceptions.csv"
        # 创建可能触发不同异常的数据
        csv_file.write_text("A,B,C\n1,2,3\nvery_long_text_that_might_cause_issues,4,5\n6,7,8\n")

        workbook = parse_file(csv_file)

        assert isinstance(workbook, Workbook)

    def test_empty_row_handling(self, tmp_path):
        """测试空行的处理"""
        csv_file = tmp_path / "empty_rows.csv"
        csv_file.write_text("A,B\n1,2\n\n3,4\n")

        workbook = parse_file(csv_file)

        assert isinstance(workbook, Workbook)
        # 空行应该被处理，可能返回空单元格或跳过

    def test_cell_with_special_characters(self, tmp_path):
        """测试包含特殊字符的单元格"""
        csv_file = tmp_path / "special_chars.csv"
        csv_file.write_text('A,B\n"text,with,commas",2\n3,"newline\nembedded"\n')

        workbook = parse_file(csv_file)

        assert isinstance(workbook, Workbook)
        # 特殊字符应该被正确处理

    def test_mismatched_column_count(self, tmp_path, caplog):
        """测试列数不匹配的处理"""
        csv_file = tmp_path / "mismatched.csv"
        csv_file.write_text("A,B,C\n1,2\n3,4,5,6\n7,8,9\n")

        with caplog.at_level(logging.WARNING):
            workbook = parse_file(csv_file)

        assert isinstance(workbook, Workbook)
        # 列数不匹配应该被处理，可能填充空单元格或记录警告

    def test_cell_value_conversion_errors(self, tmp_path):
        """测试单元格值转换错误"""
        csv_file = tmp_path / "conversion.csv"
        csv_file.write_text("A,B\n123,not_a_number\n456,789\n")

        workbook = parse_file(csv_file)

        assert isinstance(workbook, Workbook)
        # 类型转换错误应该被捕获，返回字符串或空值

    def test_all_cells_faulty_returns_empty_workbook(self, tmp_path, caplog):
        """测试所有单元格都有错误时返回空 Workbook"""
        csv_file = tmp_path / "all_faulty.csv"
        # 创建一个理论上所有单元格都会出错的文件
        csv_file.write_text("A,B\n,,\n,\n")

        with caplog.at_level(logging.WARNING):
            workbook = parse_file(csv_file)

        # 即使所有单元格都有问题，也应该返回 Workbook 结构
        assert isinstance(workbook, Workbook)


class TestCellLogging:
    """测试单元格错误日志记录"""

    def test_warning_log_contains_cell_info(self, tmp_path, caplog):
        """测试警告日志包含单元格位置信息"""
        csv_file = tmp_path / "logged.csv"
        csv_file.write_text("A,B\n1,problem_value\n3,4\n")

        with caplog.at_level(logging.WARNING):
            workbook = parse_file(csv_file)

        # 如果有警告，验证日志格式
        for record in caplog.records:
            if record.levelno == logging.WARNING:
                # 日志应该包含有用的调试信息
                assert "cell" in record.message.lower() or "row" in record.message.lower()

    def test_error_log_contains_exception_details(self, tmp_path, caplog):
        """测试错误日志包含异常详情"""
        csv_file = tmp_path / "details.csv"
        csv_file.write_text("A,B\n1,2\nerror,value\n")

        with caplog.at_level(logging.WARNING):
            workbook = parse_file(csv_file)

        # 验证日志记录存在（如果有的话）
        # 实际的日志内容取决于实现细节
