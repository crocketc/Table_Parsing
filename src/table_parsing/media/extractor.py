"""媒体提取器 - 从 XLSX 文件中提取嵌入的图片"""

import logging
from io import BytesIO
from pathlib import Path
from typing import List

import openpyxl
from openpyxl.utils import get_column_letter
from PIL import Image

from ..ir.model import MediaObject

logger = logging.getLogger(__name__)


class MediaExtractor:
    """
    从 XLSX 文件中提取嵌入的图片

    使用 openpyxl 读取 XLSX 文件中的图片对象，
    并将其转换为 MediaObject 列表。

    Features:
    - 提取所有嵌入图片
    - 保存原始图片数据
    - 检测图片格式
    - 记录锚点位置（行列坐标）
    """

    def extract_from_xlsx(self, file_path: Path) -> List[MediaObject]:
        """
        从 XLSX 文件中提取所有嵌入的图片

        Args:
            file_path: XLSX 文件路径

        Returns:
            MediaObject 列表，按图片在文件中的顺序排列

        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 文件格式不正确
        """
        path = Path(file_path)

        # 检查文件是否存在
        if not path.exists():
            raise FileNotFoundError(f"XLSX file not found: {file_path}")

        # 检查文件扩展名
        if path.suffix.lower() not in (".xlsx", ".xlsm"):
            raise ValueError(
                f"Invalid file extension: {path.suffix}. Expected .xlsx or .xlsm"
            )

        try:
            # 使用 openpyxl 加载工作簿
            wb = openpyxl.load_workbook(path)

            media_objects = []

            # 遍历所有工作表
            for sheet in wb.worksheets:
                # 提取当前工作表中的图片
                sheet_images = self._extract_images_from_sheet(sheet)
                media_objects.extend(sheet_images)

            wb.close()

            logger.info(f"Extracted {len(media_objects)} media objects from {file_path}")

            return media_objects

        except Exception as e:
            if isinstance(e, (FileNotFoundError, ValueError)):
                raise
            raise ValueError(f"Failed to extract media from XLSX file: {e}") from e

    def _extract_images_from_sheet(
        self, sheet: openpyxl.worksheet.worksheet.Worksheet
    ) -> List[MediaObject]:
        """
        从单个工作表中提取图片

        Args:
            sheet: openpyxl Worksheet 对象

        Returns:
            MediaObject 列表
        """
        media_objects = []

        # 检查工作表是否包含图片
        if not hasattr(sheet, "_images") or not sheet._images:
            return media_objects

        # 遍历所有图片
        for img in sheet._images:
            try:
                media_object = self._parse_image(img)
                if media_object:
                    media_objects.append(media_object)
            except Exception as e:
                logger.warning(f"Failed to parse image in sheet {sheet.title}: {e}")
                # 继续处理其他图片
                continue

        return media_objects

    def _parse_image(self, img: openpyxl.drawing.image.Image) -> MediaObject | None:
        """
        解析单个图片对象

        Args:
            img: openpyxl Image 对象

        Returns:
            MediaObject 对象，如果解析失败则返回 None
        """
        # 获取图片原始数据
        raw_data = self._get_image_raw_data(img)
        if not raw_data:
            logger.warning("Could not extract raw data from image")
            return None

        # 检测图片格式
        raw_format = self._detect_image_format(raw_data)

        # 获取锚点位置
        anchor_row, anchor_col = self._parse_anchor_position(img)

        return MediaObject(
            type="image",
            anchor_row=anchor_row,
            anchor_col=anchor_col,
            raw_data=raw_data,
            raw_format=raw_format,
        )

    def _get_image_raw_data(self, img: openpyxl.drawing.image.Image) -> bytes | None:
        """
        获取图片的原始字节数据

        Args:
            img: openpyxl Image 对象

        Returns:
            图片字节数据，如果获取失败则返回 None
        """
        try:
            # openpyxl Image 对象的 _data() 方法返回原始字节数据
            if hasattr(img, "_data"):
                return img._data()
            # 备选方法：通过 ref 属性访问
            elif hasattr(img, "ref"):
                return img.ref
            else:
                logger.warning("Image object has no _data or ref attribute")
                return None
        except Exception as e:
            logger.warning(f"Failed to extract image raw data: {e}")
            return None

    def _detect_image_format(self, raw_data: bytes) -> str:
        """
        检测图片格式

        Args:
            raw_data: 图片字节数据

        Returns:
            图片格式（png、jpeg 等）
        """
        try:
            img = Image.open(BytesIO(raw_data))
            format_lower = img.format.lower() if img.format else "png"

            # 统一格式名称
            if format_lower == "jpg":
                return "jpeg"
            return format_lower
        except Exception:
            # 默认返回 png
            return "png"

    def _parse_anchor_position(
        self, img: openpyxl.drawing.image.Image
    ) -> tuple[int, int]:
        """
        解析图片的锚点位置

        Args:
            img: openpyxl Image 对象

        Returns:
            (row, col) 元组，行列索引从1开始
        """
        try:
            # 获取锚点位置
            anchor = img.anchor

            # 检查是否是 OneCellAnchor 或 TwoCellAnchor 对象（从文件加载时）
            # 这些对象有 _from 属性，包含 col 和 row（0-based）
            if hasattr(anchor, "_from"):
                from_pos = anchor._from
                if hasattr(from_pos, "col") and hasattr(from_pos, "row"):
                    # openpyxl 使用 0-based 索引，需要转换为 1-based
                    col = from_pos.col + 1
                    row = from_pos.row + 1
                    return (row, col)

            if isinstance(anchor, str):
                # 如果是字符串格式（如 "A1"），解析为行列索引
                col = 1
                row = 1

                # 提取列字母和行号
                col_letters = ""
                row_digits = ""

                for char in anchor:
                    if char.isalpha():
                        col_letters += char
                    elif char.isdigit():
                        row_digits += char

                if col_letters:
                    # 将列字母转换为数字（A=1, B=2, ..., Z=26, AA=27, ...）
                    col = 0
                    for char in col_letters:
                        col = col * 26 + (ord(char.upper()) - ord("A") + 1)

                if row_digits:
                    row = int(row_digits)

                return (row, col)

            elif isinstance(anchor, (tuple, list)) and len(anchor) >= 2:
                # 如果是元组或列表格式
                # openpyxl 可能返回 (col, row) 或 (row, col)
                # 尝试两种方式
                if isinstance(anchor[0], int) and isinstance(anchor[1], int):
                    # 假设是 (col, row) 格式（Excel 坐标习惯）
                    return (anchor[1], anchor[0])

            elif hasattr(anchor, "row") and hasattr(anchor, "col"):
                # 如果是对象格式，直接获取行列索引
                return (int(anchor.row), int(anchor.col))

            # 默认位置
            logger.warning(f"Could not parse anchor position: {anchor}")
            return (1, 1)

        except Exception as e:
            logger.warning(f"Failed to parse anchor position: {e}")
            return (1, 1)
