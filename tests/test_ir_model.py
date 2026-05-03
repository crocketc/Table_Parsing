"""测试 IR 数据模型"""

import pytest
from base64 import b64decode, b64encode

from table_parsing.ir import MediaObject


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
