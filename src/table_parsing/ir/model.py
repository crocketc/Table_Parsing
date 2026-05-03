"""IR (Intermediate Representation) 数据模型"""

import datetime
from base64 import b64encode
from dataclasses import dataclass
from typing import Any, Literal, Optional, Union


@dataclass
class MediaObject:
    """媒体对象（图片或图表）"""

    type: Literal["image", "chart"]
    anchor_row: int
    anchor_col: int
    raw_data: Optional[bytes] = None
    raw_format: Optional[str] = None
    description: Optional[str] = None
    chart_metadata: Optional[dict[str, Any]] = None

    def __post_init__(self):
        """验证 type 字段必须是 'image' 或 'chart'"""
        if self.type not in ("image", "chart"):
            raise ValueError(
                f"MediaObject.type must be 'image' or 'chart', got '{self.type}'"
            )

    def to_dict(self) -> dict[str, Any]:
        """转换为 dict，bytes 转 base64"""
        result = {
            "type": self.type,
            "anchor_row": self.anchor_row,
            "anchor_col": self.anchor_col,
        }
        if self.raw_data is not None:
            result["raw_data"] = b64encode(self.raw_data).decode()
        if self.raw_format is not None:
            result["raw_format"] = self.raw_format
        if self.description is not None:
            result["description"] = self.description
        if self.chart_metadata is not None:
            result["chart_metadata"] = self.chart_metadata
        return result


@dataclass
class Cell:
    """单元格数据"""

    value: Union[str, int, float, bool, datetime.date, datetime.datetime, bytes, None]
    raw_value: Optional[str] = None
    data_type: Literal["number", "string", "date", "bool", "blank"] = "string"
    is_formula: bool = False
    formula_text: Optional[str] = None
    is_merged: bool = False
    merge_range: Optional[str] = None
    is_hidden: bool = False
    style: Optional[dict[str, Any]] = None
    embedded_media: Optional[MediaObject] = None

    def __post_init__(self):
        """验证 data_type 字段必须是有效值"""
        valid_types = {"number", "string", "date", "bool", "blank"}
        if self.data_type not in valid_types:
            raise ValueError(
                f"Cell.data_type must be one of {valid_types}, got '{self.data_type}'"
            )

    def to_dict(self) -> dict[str, Any]:
        """转换为 dict，datetime/date 转 ISO 字符串，bytes 转 base64"""
        result: dict[str, Any] = {}

        # 处理 value：datetime/date → ISO，bytes → base64
        if isinstance(self.value, datetime.datetime):
            result["value"] = self.value.isoformat()
        elif isinstance(self.value, datetime.date):
            result["value"] = self.value.isoformat()
        elif isinstance(self.value, bytes):
            result["value"] = b64encode(self.value).decode()
        else:
            result["value"] = self.value

        # 添加非默认值字段
        if self.data_type != "string":
            result["data_type"] = self.data_type
        if self.raw_value is not None:
            result["raw_value"] = self.raw_value
        if self.is_formula:
            result["is_formula"] = True
        if self.formula_text is not None:
            result["formula_text"] = self.formula_text
        if self.is_merged:
            result["is_merged"] = True
        if self.merge_range is not None:
            result["merge_range"] = self.merge_range
        if self.is_hidden:
            result["is_hidden"] = True
        if self.style is not None:
            result["style"] = self.style
        if self.embedded_media is not None:
            result["embedded_media"] = self.embedded_media.to_dict()

        return result
