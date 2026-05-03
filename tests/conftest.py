"""测试配置和 fixtures"""
import pytest
from pathlib import Path


@pytest.fixture
def sample_csv(tmp_path):
    """创建测试用的 CSV 文件"""
    csv_file = tmp_path / "sample.csv"
    csv_file.write_text("A,B,C\n1,2,3\n4,5,6", encoding="utf-8")
    return csv_file


@pytest.fixture
def sample_config(tmp_path):
    """创建测试用的配置文件"""
    config_file = tmp_path / ".table-parse.yml"
    config_file.write_text("output_format: yaml\npretty: false\n", encoding="utf-8")
    return config_file


@pytest.fixture
def sample_xlsx(tmp_path):
    """创建测试用的 XLSX 文件"""
    try:
        from openpyxl import Workbook

        xlsx_file = tmp_path / "sample.xlsx"
        wb = Workbook()
        ws = wb.active
        ws.title = "Sheet1"

        # 添加数据
        ws.append(["A", "B", "C"])
        ws.append([1, 2, 3])
        ws.append([4, 5, 6])

        wb.save(xlsx_file)
        return xlsx_file
    except ImportError:
        pytest.skip("openpyxl not installed")
