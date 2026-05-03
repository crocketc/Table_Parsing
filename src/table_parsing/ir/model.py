"""IR (Intermediate Representation) 数据模型"""

from base64 import b64encode
from dataclasses import dataclass
from typing import Any, Literal, Optional


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
