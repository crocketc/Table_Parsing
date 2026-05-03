"""媒体 AI 理解 - 使用多模态模型理解嵌入图片的内容"""

import asyncio
import logging
from typing import List

from ..ir.model import MediaObject, Workbook
from ..model_client.base import ModelClient

logger = logging.getLogger(__name__)


class MediaUnderstanding:
    """
    使用多模态模型理解嵌入图片和图表的内容

    通过 ModelClient 调用多模态大模型 API，
    为每个 MediaObject 生成文本描述。

    Features:
    - 批量并发处理多个媒体对象
    - 优雅的错误处理（单个失败不影响整体）
    - 将描述文本回填到 MediaObject.description
    - 支持处理 Workbook 中的所有媒体
    """

    def __init__(self, client: ModelClient):
        """
        初始化

        Args:
            client: 模型 API 客户端
        """
        self._client = client

    async def understand_media(self, media: MediaObject) -> MediaObject:
        """
        理解单个媒体对象

        Args:
            media: MediaObject 对象

        Returns:
            添加了 description 的 MediaObject 对象（原对象修改）
        """
        try:
            # 检查是否有原始数据
            if media.raw_data is None:
                logger.warning(f"Media at ({media.anchor_row}, {media.anchor_col}) has no raw_data")
                return media

            # 构建提示词
            messages = [
                {
                    "role": "user",
                    "content": "请简要描述这张图片的内容。如果是图表，请说明图表类型和数据趋势。",
                }
            ]

            # 调用模型 API
            description = await self._client.complete(messages, [media.raw_data])

            # 更新 MediaObject 的描述
            media.description = description

            logger.debug(f"Successfully understood media at ({media.anchor_row}, {media.anchor_col})")

        except Exception as e:
            logger.warning(f"Failed to understand media at ({media.anchor_row}, {media.anchor_col}): {e}")
            # 保持 media.description 为 None

        return media

    async def understand_batch(self, media_objects: List[MediaObject]) -> List[MediaObject]:
        """
        批量理解多个媒体对象

        Args:
            media_objects: MediaObject 列表

        Returns:
            添加了 description 的 MediaObject 列表
        """
        if not media_objects:
            return []

        # 并发处理所有媒体对象
        tasks = [self.understand_media(media) for media in media_objects]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理异常结果
        processed_results: List[MediaObject] = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.warning(f"Failed to process media {i}: {result}")
                # 保持原始 MediaObject，description 为 None
                processed_results.append(media_objects[i])
            elif isinstance(result, MediaObject):
                processed_results.append(result)

        logger.info(f"Processed {len(processed_results)} media objects")

        return processed_results

    async def understand_workbook(self, workbook: Workbook) -> Workbook:
        """
        理解 Workbook 中的所有媒体对象

        遍历 Workbook 的所有 Sheet 和 Cell，找出所有 MediaObject，
        批量理解后回填到原对象。

        Args:
            workbook: Workbook 对象

        Returns:
            同一个 Workbook 对象（修改了其中的 MediaObject）
        """
        # 收集所有 MediaObject
        all_media = []

        assert workbook.sheets is not None  # __post_init__ 确保此字段不为 None
        for sheet in workbook.sheets:
            assert sheet.cells is not None  # __post_init__ 确保此字段不为 None
            for row in sheet.cells:
                for cell in row:
                    if hasattr(cell, "embedded_media") and cell.embedded_media is not None:
                        all_media.append(cell.embedded_media)

        if not all_media:
            logger.info("No media objects found in workbook")
            return workbook

        logger.info(f"Found {len(all_media)} media objects in workbook")

        # 批量理解
        await self.understand_batch(all_media)

        return workbook
