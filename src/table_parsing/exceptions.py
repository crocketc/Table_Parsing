"""
Table Parsing IR 自定义异常层级
"""


class TableParsingError(Exception):
    """Table Parsing IR 所有异常的基类"""

    pass


class UnsupportedFormatError(TableParsingError):
    """不支持的文件格式"""

    def __init__(self, extension: str, supported: list[str]):
        self.extension = extension
        self.supported = supported
        super().__init__(
            f"Unsupported format: {extension}. "
            f"Supported formats: {', '.join(supported)}"
        )


class FileFormatMismatchError(TableParsingError):
    """文件扩展名与实际格式不匹配"""

    def __init__(self, extension: str, actual_format: str):
        self.extension = extension
        self.actual_format = actual_format
        super().__init__(
            f"File format mismatch: extension is {extension} "
            f"but actual format is {actual_format}"
        )


class FileProtectedError(TableParsingError):
    """文件受密码保护"""

    def __init__(self, file_path: str):
        self.file_path = file_path
        super().__init__(f"File is protected: {file_path}")


class ParseError(TableParsingError):
    """通用解析错误"""

    pass
