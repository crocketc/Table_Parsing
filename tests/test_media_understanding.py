"""测试媒体 AI 理解"""

import asyncio
from io import BytesIO
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import openpyxl
import pytest
from PIL import Image

from table_parsing.ir.model import MediaObject, Workbook
from table_parsing.media.understanding import MediaUnderstanding
from table_parsing.model_client import ModelClient


@pytest.fixture
def sample_image():
    """创建示例图片"""
    img = Image.new("RGB", (100, 100), color="red")
    img_io = BytesIO()
    img.save(img_io, format="PNG")
    return img_io.getvalue()


@pytest.fixture
def sample_media_objects(sample_image: bytes):
    """创建示例 MediaObject 列表"""
    return [
        MediaObject(
            type="image",
            anchor_row=1,
            anchor_col=1,
            raw_data=sample_image,
            raw_format="png",
        ),
        MediaObject(
            type="image",
            anchor_row=3,
            anchor_col=5,
            raw_data=sample_image,
            raw_format="png",
        ),
    ]


@pytest.fixture
def mock_client():
    """创建模拟 ModelClient"""
    client = Mock(spec=ModelClient)

    # 设置异步的 complete 方法
    async def mock_complete(messages, images):
        # 模拟 AI 返回描述
        return f"这是一个图片，包含 {len(images)} 张图片"

    client.complete = AsyncMock(side_effect=mock_complete)
    return client


class TestMediaUnderstanding:
    """测试 MediaUnderstanding 基础功能"""

    def test_understanding_creation(self, mock_client):
        """测试创建理解器实例"""
        understanding = MediaUnderstanding(mock_client)
        assert understanding is not None
        assert understanding._client == mock_client

    @pytest.mark.asyncio
    async def test_understand_single_media(self, mock_client, sample_image: bytes):
        """测试理解单个媒体对象"""
        media = MediaObject(
            type="image",
            anchor_row=1,
            anchor_col=1,
            raw_data=sample_image,
            raw_format="png",
        )

        understanding = MediaUnderstanding(mock_client)
        result = await understanding.understand_media(media)

        assert isinstance(result, MediaObject)
        assert result.description is not None
        assert "图片" in result.description
        assert result.raw_data == media.raw_data

    @pytest.mark.asyncio
    async def test_understand_batch_media(
        self, mock_client, sample_media_objects: list[MediaObject]
    ):
        """测试批量理解媒体对象"""
        understanding = MediaUnderstanding(mock_client)
        results = await understanding.understand_batch(sample_media_objects)

        assert len(results) == 2
        for media in results:
            assert media.description is not None
            assert "图片" in media.description

    @pytest.mark.asyncio
    async def test_understand_workbook_media(
        self, mock_client, sample_media_objects: list[MediaObject]
    ):
        """测试理解 Workbook 中的所有媒体"""
        # 创建包含媒体的 Workbook
        sheet = Mock()
        sheet.name = "Sheet1"
        sheet.cells = [[Mock(embedded_media=media) for media in sample_media_objects]]

        workbook = Mock(spec=Workbook)
        workbook.sheets = [sheet]

        understanding = MediaUnderstanding(mock_client)
        result_workbook = await understanding.understand_workbook(workbook)

        # 验证 Workbook 中的媒体都被添加了描述
        assert result_workbook is workbook  # 应该返回同一个对象

    @pytest.mark.asyncio
    async def test_empty_media_list(self, mock_client):
        """测试处理空的媒体列表"""
        understanding = MediaUnderstanding(mock_client)
        results = await understanding.understand_batch([])

        assert results == []

    @pytest.mark.asyncio
    async def test_api_error_handling(self, mock_client, sample_image: bytes):
        """测试 API 错误时的优雅处理"""
        # 设置 mock 抛出异常
        async def raise_error(*args, **kwargs):
            raise Exception("API Error")

        mock_client.complete = AsyncMock(side_effect=raise_error)

        media = MediaObject(
            type="image",
            anchor_row=1,
            anchor_col=1,
            raw_data=sample_image,
            raw_format="png",
        )

        understanding = MediaUnderstanding(mock_client)
        result = await understanding.understand_media(media)

        # 应该跳过失败的媒体，但仍然返回 MediaObject
        assert isinstance(result, MediaObject)
        assert result.description is None  # 没有描述

    @pytest.mark.asyncio
    async def test_partial_batch_failure(
        self, mock_client, sample_media_objects: list[MediaObject]
    ):
        """测试批量处理时的部分失败"""
        # 设置第一次调用成功，第二次调用失败
        call_count = 0

        async def conditional_complete(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return "成功的描述"
            else:
                raise Exception("API Error")

        mock_client.complete = AsyncMock(side_effect=conditional_complete)

        understanding = MediaUnderstanding(mock_client)
        results = await understanding.understand_batch(sample_media_objects)

        # 应该有两个结果，一个有描述，一个没有
        assert len(results) == 2
        assert results[0].description == "成功的描述"
        assert results[1].description is None


class TestMediaUnderstandingIntegration:
    """测试 MediaUnderstanding 集成功能"""

    @pytest.mark.asyncio
    async def test_concurrent_processing(self, sample_media_objects: list[MediaObject]):
        """测试并发处理多个媒体"""
        # 创建真实的异步 mock
        client = Mock(spec=ModelClient)

        async def slow_complete(messages, images):
            await asyncio.sleep(0.1)  # 模拟网络延迟
            return f"描述 {len(images)} 张图片"

        client.complete = AsyncMock(side_effect=slow_complete)

        understanding = MediaUnderstanding(client)

        import time

        start = time.time()
        results = await understanding.understand_batch(sample_media_objects)
        elapsed = time.time() - start

        assert len(results) == 2
        # 并发处理应该比串行快
        # 串行需要 0.2 秒，并发应该只需要约 0.1 秒
        assert elapsed < 0.15

    @pytest.mark.asyncio
    async def test_preserves_media_attributes(
        self, mock_client, sample_image: bytes
    ):
        """测试理解过程保持媒体对象的属性"""
        media = MediaObject(
            type="image",
            anchor_row=5,
            anchor_col=10,
            raw_data=sample_image,
            raw_format="png",
        )

        understanding = MediaUnderstanding(mock_client)
        result = await understanding.understand_media(media)

        # 验证所有原始属性都被保留
        assert result.type == media.type
        assert result.anchor_row == media.anchor_row
        assert result.anchor_col == media.anchor_col
        assert result.raw_data == media.raw_data
        assert result.raw_format == media.raw_format
        # 只有 description 被添加
        assert result.description is not None

    @pytest.mark.asyncio
    async def test_different_image_formats(self, mock_client):
        """测试处理不同格式的图片"""
        # 创建 PNG 和 JPEG 图片
        png_img = Image.new("RGB", (50, 50), color="red")
        png_io = BytesIO()
        png_img.save(png_io, format="PNG")

        jpeg_img = Image.new("RGB", (50, 50), color="blue")
        jpeg_io = BytesIO()
        jpeg_img.save(jpeg_io, format="JPEG")

        media_objects = [
            MediaObject(
                type="image",
                anchor_row=1,
                anchor_col=1,
                raw_data=png_io.getvalue(),
                raw_format="png",
            ),
            MediaObject(
                type="image",
                anchor_row=2,
                anchor_col=1,
                raw_data=jpeg_io.getvalue(),
                raw_format="jpeg",
            ),
        ]

        understanding = MediaUnderstanding(mock_client)
        results = await understanding.understand_batch(media_objects)

        assert len(results) == 2
        for media in results:
            assert media.description is not None
