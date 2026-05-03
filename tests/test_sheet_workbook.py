"""测试 Sheet 和 Workbook 数据模型"""

import datetime
import pytest

from table_parsing.ir import Cell, MediaObject, Sheet, Workbook


class TestSheet:
    """测试 Sheet 数据类"""

    def test_sheet_creation_with_defaults(self):
        """测试创建 Sheet 并验证默认值"""
        sheet = Sheet(name="测试工作表")

        assert sheet.name == "测试工作表"
        assert sheet.hidden is False
        assert sheet.max_row == 0
        assert sheet.max_col == 0
        assert sheet.cells == []

    def test_sheet_with_all_fields(self):
        """测试完整字段创建 Sheet"""
        cells = [
            [Cell(value="A1"), Cell(value="B1")],
            [Cell(value="A2"), Cell(value="B2")],
        ]

        sheet = Sheet(
            name="销售数据",
            hidden=False,
            max_row=2,
            max_col=2,
            cells=cells,
        )

        assert sheet.name == "销售数据"
        assert sheet.hidden is False
        assert sheet.max_row == 2
        assert sheet.max_col == 2
        assert len(sheet.cells) == 2
        assert len(sheet.cells[0]) == 2

    def test_sheet_hidden_property(self):
        """测试 hidden 属性"""
        visible_sheet = Sheet(name="可见", hidden=False)
        hidden_sheet = Sheet(name="隐藏", hidden=True)

        assert visible_sheet.hidden is False
        assert hidden_sheet.hidden is True

    def test_sheet_with_empty_cells(self):
        """测试空 cells 列表"""
        sheet = Sheet(name="空表", max_row=0, max_col=0)

        assert sheet.cells == []
        assert sheet.max_row == 0
        assert sheet.max_col == 0

    def test_sheet_to_dict_simple(self):
        """测试 to_dict 序列化简单 cells"""
        cells = [
            [Cell(value="姓名"), Cell(value="年龄")],
            [Cell(value="张三", data_type="string"), Cell(value=25, data_type="number")],
        ]

        sheet = Sheet(name="员工信息", max_row=2, max_col=2, cells=cells)

        result = sheet.to_dict()

        assert result["name"] == "员工信息"
        assert result["hidden"] is False
        assert result["max_row"] == 2
        assert result["max_col"] == 2
        assert len(result["cells"]) == 2
        assert result["cells"][0][0]["value"] == "姓名"
        assert result["cells"][1][0]["value"] == "张三"
        assert result["cells"][1][1]["value"] == 25
        assert result["cells"][1][1]["data_type"] == "number"

    def test_sheet_to_dict_with_complex_cells(self):
        """测试 to_dict 序列化包含复杂 Cell 的 Sheet"""
        media = MediaObject(
            type="chart", anchor_row=0, anchor_col=0, description="销售图表"
        )
        cells = [
            [
                Cell(
                    value="销售额",
                    data_type="number",
                    is_formula=True,
                    formula_text="=SUM(A1:A10)",
                    embedded_media=media,
                )
            ]
        ]

        sheet = Sheet(name="财务报表", max_row=1, max_col=1, cells=cells)

        result = sheet.to_dict()

        assert result["name"] == "财务报表"
        assert result["cells"][0][0]["value"] == "销售额"
        assert result["cells"][0][0]["data_type"] == "number"
        assert result["cells"][0][0]["is_formula"] is True
        assert result["cells"][0][0]["formula_text"] == "=SUM(A1:A10)"
        assert result["cells"][0][0]["embedded_media"]["type"] == "chart"

    def test_sheet_to_dict_with_datetime_cells(self):
        """测试 to_dict 序列化包含 datetime 的 cells"""
        dt = datetime.datetime(2024, 5, 3, 14, 30)
        cells = [[Cell(value=dt, data_type="date")]]

        sheet = Sheet(name="日期测试", max_row=1, max_col=1, cells=cells)

        result = sheet.to_dict()

        assert result["cells"][0][0]["value"] == "2024-05-03T14:30:00"

    def test_sheet_to_dict_hidden(self):
        """测试 to_dict 序列化 hidden 属性"""
        sheet = Sheet(name="隐藏表", hidden=True)

        result = sheet.to_dict()

        assert result["hidden"] is True


class TestWorkbook:
    """测试 Workbook 数据类"""

    def test_workbook_creation_with_defaults(self):
        """测试创建 Workbook 并验证默认值"""
        workbook = Workbook()

        assert workbook.metadata == {}
        assert workbook.sheets == []

    def test_workbook_with_metadata(self):
        """测试带 metadata 的 Workbook"""
        metadata = {
            "title": "年度报告",
            "author": "张三",
            "created": "2024-05-03",
            "version": "1.0",
        }

        workbook = Workbook(metadata=metadata)

        assert workbook.metadata == metadata
        assert workbook.sheets == []

    def test_workbook_with_sheets(self):
        """测试包含 sheets 的 Workbook"""
        cells1 = [[Cell(value="A1"), Cell(value="B1")]]
        cells2 = [[Cell(value="X1"), Cell(value="Y1")]]

        sheet1 = Sheet(name="Sheet1", max_row=1, max_col=2, cells=cells1)
        sheet2 = Sheet(name="Sheet2", max_row=1, max_col=2, cells=cells2)

        workbook = Workbook(sheets=[sheet1, sheet2])

        assert len(workbook.sheets) == 2
        assert workbook.sheets[0].name == "Sheet1"
        assert workbook.sheets[1].name == "Sheet2"

    def test_workbook_with_all_fields(self):
        """测试完整字段创建 Workbook"""
        metadata = {"title": "测试工作簿"}
        cells = [[Cell(value="数据")]]
        sheet = Sheet(name="工作表1", max_row=1, max_col=1, cells=cells)

        workbook = Workbook(metadata=metadata, sheets=[sheet])

        assert workbook.metadata == metadata
        assert len(workbook.sheets) == 1
        assert workbook.sheets[0].name == "工作表1"

    def test_workbook_to_dict_empty(self):
        """测试空 Workbook 的 to_dict 序列化"""
        workbook = Workbook()

        result = workbook.to_dict()

        assert result == {"metadata": {}, "sheets": []}

    def test_workbook_to_dict_with_metadata_only(self):
        """测试仅包含 metadata 的 to_dict 序列化"""
        metadata = {
            "title": "销售报告",
            "department": "财务部",
            "year": 2024,
        }

        workbook = Workbook(metadata=metadata)

        result = workbook.to_dict()

        assert result["metadata"] == metadata
        assert result["sheets"] == []

    def test_workbook_to_dict_with_sheets(self):
        """测试包含 sheets 的 to_dict 序列化"""
        cells = [
            [Cell(value="产品"), Cell(value="销量")],
            [Cell(value="A"), Cell(value=100, data_type="number")],
        ]
        sheet = Sheet(name="销售数据", max_row=2, max_col=2, cells=cells)

        workbook = Workbook(sheets=[sheet])

        result = workbook.to_dict()

        assert result["metadata"] == {}
        assert len(result["sheets"]) == 1
        assert result["sheets"][0]["name"] == "销售数据"
        assert result["sheets"][0]["max_row"] == 2
        assert result["sheets"][0]["max_col"] == 2
        assert result["sheets"][0]["cells"][0][0]["value"] == "产品"
        assert result["sheets"][0]["cells"][1][1]["value"] == 100
        assert result["sheets"][0]["cells"][1][1]["data_type"] == "number"

    def test_workbook_to_dict_complete(self):
        """测试完整 Workbook 的 to_dict 序列化"""
        metadata = {"title": "完整工作簿", "version": "2.0"}

        cells1 = [[Cell(value="表1-数据")]]
        cells2 = [[Cell(value="表2-数据")]]

        sheet1 = Sheet(name="工作表1", max_row=1, max_col=1, cells=cells1)
        sheet2 = Sheet(name="工作表2", hidden=True, max_row=1, max_col=1, cells=cells2)

        workbook = Workbook(metadata=metadata, sheets=[sheet1, sheet2])

        result = workbook.to_dict()

        # 验证 metadata
        assert result["metadata"]["title"] == "完整工作簿"
        assert result["metadata"]["version"] == "2.0"

        # 验证 sheets
        assert len(result["sheets"]) == 2
        assert result["sheets"][0]["name"] == "工作表1"
        assert result["sheets"][0]["hidden"] is False
        assert result["sheets"][0]["cells"][0][0]["value"] == "表1-数据"

        assert result["sheets"][1]["name"] == "工作表2"
        assert result["sheets"][1]["hidden"] is True
        assert result["sheets"][1]["cells"][0][0]["value"] == "表2-数据"

    def test_workbook_to_dict_with_complex_nested_structure(self):
        """测试复杂嵌套结构的 to_dict 序列化"""
        # 创建包含 MediaObject 的复杂 Cell
        media = MediaObject(
            type="image",
            anchor_row=0,
            anchor_col=0,
            raw_data=b"fake_image",
            raw_format="png",
        )

        cells = [
            [
                Cell(
                    value="标题",
                    style={"font": "Arial", "size": 14, "bold": True},
                ),
                Cell(
                    value=2024,
                    data_type="number",
                    is_formula=True,
                    formula_text="=YEAR(NOW())",
                ),
            ],
            [
                Cell(
                    value="图表",
                    embedded_media=media,
                ),
                Cell(
                    value=datetime.date(2024, 5, 3),
                    data_type="date",
                ),
            ],
        ]

        sheet = Sheet(name="综合测试", max_row=2, max_col=2, cells=cells)
        metadata = {"title": "综合测试工作簿", "author": "测试用户"}

        workbook = Workbook(metadata=metadata, sheets=[sheet])

        result = workbook.to_dict()

        # 验证深层嵌套结构
        assert result["metadata"]["author"] == "测试用户"
        assert result["sheets"][0]["name"] == "综合测试"

        # 第一行
        assert result["sheets"][0]["cells"][0][0]["value"] == "标题"
        assert result["sheets"][0]["cells"][0][0]["style"]["font"] == "Arial"
        assert result["sheets"][0]["cells"][0][1]["value"] == 2024
        assert result["sheets"][0]["cells"][0][1]["is_formula"] is True

        # 第二行
        assert result["sheets"][0]["cells"][1][0]["value"] == "图表"
        assert result["sheets"][0]["cells"][1][0]["embedded_media"]["type"] == "image"
        assert result["sheets"][0]["cells"][1][0]["embedded_media"]["raw_format"] == "png"
        assert result["sheets"][0]["cells"][1][1]["value"] == "2024-05-03"

    def test_workbook_to_dict_preserves_metadata_types(self):
        """测试 to_dict 保留 metadata 的各种数据类型"""
        metadata = {
            "string": "文本",
            "number": 42,
            "float": 3.14,
            "bool": True,
            "null": None,
            "list": [1, 2, 3],
            "nested": {"key": "value"},
        }

        workbook = Workbook(metadata=metadata)

        result = workbook.to_dict()

        # 验证所有数据类型都被保留
        assert result["metadata"]["string"] == "文本"
        assert result["metadata"]["number"] == 42
        assert result["metadata"]["float"] == 3.14
        assert result["metadata"]["bool"] is True
        assert result["metadata"]["null"] is None
        assert result["metadata"]["list"] == [1, 2, 3]
        assert result["metadata"]["nested"]["key"] == "value"
