"""测试 IR 数据模型"""

import datetime
import pytest
from base64 import b64decode, b64encode

from table_parsing.ir import Cell, MediaObject


class TestMediaObject:
    """测试 MediaObject 数据类"""

    def test_media_object_creation_with_defaults(self):
        """测试创建 MediaObject 并验证默认值"""
        media = MediaObject(type="image", anchor_row=0, anchor_col=1)

        assert media.type == "image"
        assert media.anchor_row == 0
        assert media.anchor_col == 1
        assert media.raw_data is None
        assert media.raw_format is None
        assert media.description is None
        assert media.chart_metadata is None

    def test_media_object_type_validation(self):
        """测试 type 字段只能是 'image' 或 'chart'"""
        # 有效类型
        MediaObject(type="image", anchor_row=0, anchor_col=0)
        MediaObject(type="chart", anchor_row=0, anchor_col=0)

        # 无效类型
        with pytest.raises(ValueError, match="MediaObject.type must be 'image' or 'chart'"):
            MediaObject(type="video", anchor_row=0, anchor_col=0)

        with pytest.raises(ValueError, match="MediaObject.type must be 'image' or 'chart'"):
            MediaObject(type="invalid", anchor_row=0, anchor_col=0)

    def test_media_object_with_all_fields(self):
        """测试完整字段创建 MediaObject"""
        raw_data = b"fake_image_data"
        description = "测试图表"
        chart_metadata = {"chart_type": "bar", "title": "销售数据"}

        media = MediaObject(
            type="chart",
            anchor_row=2,
            anchor_col=3,
            raw_data=raw_data,
            raw_format="png",
            description=description,
            chart_metadata=chart_metadata,
        )

        assert media.type == "chart"
        assert media.anchor_row == 2
        assert media.anchor_col == 3
        assert media.raw_data == raw_data
        assert media.raw_format == "png"
        assert media.description == description
        assert media.chart_metadata == chart_metadata

    def test_media_object_to_dict(self):
        """测试 to_dict 序列化，特别是 bytes → base64 转换"""
        raw_data = b"test_image_bytes"
        original_b64 = b64encode(raw_data).decode()

        media = MediaObject(
            type="image",
            anchor_row=1,
            anchor_col=2,
            raw_data=raw_data,
            raw_format="jpeg",
            description="测试图片",
        )

        result = media.to_dict()

        # 验证基本字段
        assert result["type"] == "image"
        assert result["anchor_row"] == 1
        assert result["anchor_col"] == 2
        assert result["raw_format"] == "jpeg"
        assert result["description"] == "测试图片"

        # 验证 bytes → base64 转换
        assert result["raw_data"] == original_b64
        assert isinstance(result["raw_data"], str)

        # 验证可以反向解码
        decoded = b64decode(result["raw_data"])
        assert decoded == raw_data

    def test_media_object_to_dict_minimal(self):
        """测试最小字段的 to_dict 序列化"""
        media = MediaObject(type="chart", anchor_row=0, anchor_col=0)

        result = media.to_dict()

        assert result == {
            "type": "chart",
            "anchor_row": 0,
            "anchor_col": 0,
        }

    def test_media_object_to_dict_with_chart_metadata(self):
        """测试包含 chart_metadata 的序列化"""
        metadata = {"chart_type": "line", "x_axis": "日期", "y_axis": "数值"}
        media = MediaObject(
            type="chart",
            anchor_row=0,
            anchor_col=0,
            chart_metadata=metadata,
        )

        result = media.to_dict()

        assert result["chart_metadata"] == metadata


class TestCell:
    """测试 Cell 数据类"""

    def test_cell_creation_with_defaults(self):
        """测试创建 Cell 并验证默认值"""
        cell = Cell(value="测试")

        assert cell.value == "测试"
        assert cell.raw_value is None
        assert cell.data_type == "string"
        assert cell.is_formula is False
        assert cell.formula_text is None
        assert cell.is_merged is False
        assert cell.merge_range is None
        assert cell.is_hidden is False
        assert cell.style is None
        assert cell.embedded_media is None

    def test_cell_data_type_validation(self):
        """测试 data_type 字段只能是有效值"""
        # 有效类型
        Cell(value=123, data_type="number")
        Cell(value="text", data_type="string")
        Cell(value=datetime.date(2024, 1, 1), data_type="date")
        Cell(value=True, data_type="bool")
        Cell(value=None, data_type="blank")

        # 无效类型
        with pytest.raises(ValueError, match="Cell.data_type must be one of"):
            Cell(value="test", data_type="invalid")

        with pytest.raises(ValueError, match="Cell.data_type must be one of"):
            Cell(value="test", data_type="array")

    def test_cell_with_all_fields(self):
        """测试完整字段创建 Cell"""
        media = MediaObject(type="image", anchor_row=0, anchor_col=0)
        style = {"font": "Arial", "size": 12}

        cell = Cell(
            value=42,
            raw_value="=A1+B1",
            data_type="number",
            is_formula=True,
            formula_text="=A1+B1",
            is_merged=True,
            merge_range="A1:B2",
            is_hidden=False,
            style=style,
            embedded_media=media,
        )

        assert cell.value == 42
        assert cell.raw_value == "=A1+B1"
        assert cell.data_type == "number"
        assert cell.is_formula is True
        assert cell.formula_text == "=A1+B1"
        assert cell.is_merged is True
        assert cell.merge_range == "A1:B2"
        assert cell.is_hidden is False
        assert cell.style == style
        assert cell.embedded_media == media

    def test_cell_to_dict_with_datetime(self):
        """测试 to_dict 序列化 datetime → ISO 字符串"""
        dt = datetime.datetime(2024, 5, 3, 14, 30, 0)
        cell = Cell(value=dt, data_type="date")

        result = cell.to_dict()

        assert result["value"] == "2024-05-03T14:30:00"
        assert isinstance(result["value"], str)

    def test_cell_to_dict_with_date(self):
        """测试 to_dict 序列化 date → ISO 字符串"""
        d = datetime.date(2024, 5, 3)
        cell = Cell(value=d, data_type="date")

        result = cell.to_dict()

        assert result["value"] == "2024-05-03"
        assert isinstance(result["value"], str)

    def test_cell_to_dict_with_bytes(self):
        """测试 to_dict 序列化 bytes → base64"""
        raw_data = b"test_bytes_data"
        original_b64 = b64encode(raw_data).decode()

        cell = Cell(value=raw_data, raw_value="binary", data_type="string")

        result = cell.to_dict()

        # 验证 bytes → base64 转换
        assert result["value"] == original_b64
        assert isinstance(result["value"], str)

        # 验证可以反向解码
        decoded = b64decode(result["value"])
        assert decoded == raw_data

    def test_cell_to_dict_with_embedded_media(self):
        """测试包含 embedded_media 的序列化"""
        media = MediaObject(
            type="chart",
            anchor_row=0,
            anchor_col=0,
            raw_data=b"chart_data",
            raw_format="png",
        )
        cell = Cell(value="销售额", data_type="string", embedded_media=media)

        result = cell.to_dict()

        assert result["value"] == "销售额"
        assert result["embedded_media"]["type"] == "chart"
        assert result["embedded_media"]["raw_data"] == b64encode(b"chart_data").decode()

    def test_cell_to_dict_minimal(self):
        """测试最小字段的 to_dict 序列化"""
        cell = Cell(value="简单文本")

        result = cell.to_dict()

        assert result == {"value": "简单文本"}

    def test_cell_to_dict_with_all_non_none_fields(self):
        """测试包含所有非 None 字段的序列化"""
        cell = Cell(
            value=100,
            data_type="number",
            is_formula=False,
            is_merged=False,
            is_hidden=False,
        )

        result = cell.to_dict()

        # 只包含 value 和 data_type（非默认值）
        assert result == {"value": 100, "data_type": "number"}

