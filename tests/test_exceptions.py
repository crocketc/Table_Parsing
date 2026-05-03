# tests/test_exceptions.py
import pytest

from table_parsing.exceptions import (
    TableParsingError,
    UnsupportedFormatError,
    FileFormatMismatchError,
    FileProtectedError,
    ParseError,
)


def test_table_parsing_error_is_base_exception():
    """TableParsingError 应该是所有自定义异常的基类"""
    assert issubclass(UnsupportedFormatError, TableParsingError)
    assert issubclass(FileFormatMismatchError, TableParsingError)
    assert issubclass(FileProtectedError, TableParsingError)
    assert issubclass(ParseError, TableParsingError)


def test_unsupported_format_error_message():
    """UnsupportedFormatError 应该包含格式信息"""
    exc = UnsupportedFormatError(".doc", [".csv", ".xls", ".xlsx"])
    assert ".doc" in str(exc)
    assert ".csv" in str(exc)
    assert ".xls" in str(exc)
    assert ".xlsx" in str(exc)


def test_file_format_mismatch_error_message():
    """FileFormatMismatchError 应该包含扩展名和实际格式"""
    exc = FileFormatMismatchError(".csv", "XLSX")
    assert ".csv" in str(exc)
    assert "XLSX" in str(exc)


def test_file_protected_error_message():
    """FileProtectedError 应该包含文件路径"""
    exc = FileProtectedError("secret.xlsx")
    assert "secret.xlsx" in str(exc)


def test_parse_error_message():
    """ParseError 应该支持自定义消息"""
    exc = ParseError("Custom parse error")
    assert "Custom parse error" in str(exc)


def test_exception_catch_hierarchy():
    """所有自定义异常应该能被基类捕获"""
    try:
        raise UnsupportedFormatError(".txt", [".csv"])
    except TableParsingError:
        assert True
    else:
        assert False, "Should be caught by TableParsingError"
