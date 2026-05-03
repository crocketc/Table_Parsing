"""测试模型 API 客户端"""

import base64
from io import BytesIO
from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest
from PIL import Image

from table_parsing.exceptions import TableParsingError
from table_parsing.model_client import ModelClient, OpenAICompatibleClient


class TestModelClient:
    """测试 ModelClient 协议"""

    def test_model_client_is_protocol(self):
        """ModelClient 应该是一个协议"""
        from typing import Protocol

        assert issubclass(ModelClient, Protocol)

    def test_model_client_has_complete_method(self):
        """ModelClient 应该定义 complete 方法"""
        assert hasattr(ModelClient, "complete")


class TestOpenAICompatibleClient:
    """测试 OpenAICompatibleClient 实现"""

    @pytest.fixture
    def mock_config(self):
        """创建测试配置"""
        from table_parsing.config import ModelApiConfig

        return ModelApiConfig(
            base_url="http://test.local:8000",
            model="test-model",
            api_key="test-key",
            max_concurrency=2,
        )

    @pytest.fixture
    def client(self, mock_config):
        """创建客户端实例"""
        return OpenAICompatibleClient(mock_config)

    @pytest.mark.asyncio
    async def test_init_creates_semaphore(self, client):
        """初始化应该创建信号量"""
        assert client._semaphore is not None
        assert client._semaphore._value == 2  # max_concurrency

    @pytest.mark.asyncio
    async def test_init_without_api_key(self):
        """应该支持无 API key 的初始化"""
        from table_parsing.config import ModelApiConfig

        config = ModelApiConfig(
            base_url="http://test.local:8000",
            model="test-model",
            api_key="",  # 空 API key
        )
        client = OpenAICompatibleClient(config)

        assert client._api_key == ""

    @pytest.mark.asyncio
    async def test_complete_with_text_only(self, client):
        """测试纯文本完成"""
        messages = [{"role": "user", "content": "Hello"}]

        # Mock HTTP 响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Hi there!"}}]
        }

        with patch("httpx.AsyncClient.post", return_value=mock_response) as mock_post:
            result = await client.complete(messages, [])

            mock_post.assert_called_once()
            call_args = mock_post.call_args

            # 验证 URL
            assert call_args[0][0] == "http://test.local:8000/v1/chat/completions"

            # 验证请求体
            request_data = call_args[1]["json"]
            assert request_data["model"] == "test-model"
            assert request_data["messages"] == messages
            assert request_data["max_tokens"] == 4096

            # 验证结果
            assert result == "Hi there!"

    @pytest.mark.asyncio
    async def test_complete_with_images(self, client):
        """测试带图片的完成"""
        messages = [{"role": "user", "content": "What's in this image?"}]

        # 创建测试图片
        img = Image.new("RGB", (100, 100), color="red")
        img_io = BytesIO()
        img.save(img_io, format="PNG")
        img_bytes = img_io.getvalue()
        img_b64 = base64.b64encode(img_bytes).decode()

        # Mock HTTP 响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "A red image"}}]
        }

        with patch("httpx.AsyncClient.post", return_value=mock_response) as mock_post:
            result = await client.complete(messages, [img_bytes])

            mock_post.assert_called_once()
            request_data = mock_post.call_args[1]["json"]

            # 验证图片被正确编码
            content = request_data["messages"][0]["content"]
            assert isinstance(content, list)
            assert len(content) == 2

            # 第一部分是文本
            assert content[0]["type"] == "text"

            # 第二部分是图片
            assert content[1]["type"] == "image_url"
            assert content[1]["image_url"]["url"].startswith("data:image/png;base64,")
            assert img_b64 in content[1]["image_url"]["url"]

            # 验证结果
            assert result == "A red image"

    @pytest.mark.asyncio
    async def test_complete_with_jpeg_image(self, client):
        """测试 JPEG 图片编码"""
        messages = [{"role": "user", "content": "Describe this"}]

        # 创建 JPEG 图片
        img = Image.new("RGB", (50, 50), color="blue")
        img_io = BytesIO()
        img.save(img_io, format="JPEG")
        img_bytes = img_io.getvalue()

        # Mock HTTP 响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Blue image"}}]
        }

        with patch("httpx.AsyncClient.post", return_value=mock_response) as mock_post:
            await client.complete(messages, [img_bytes])

            request_data = mock_post.call_args[1]["json"]
            content = request_data["messages"][0]["content"]

            # 验证 JPEG 格式
            assert content[1]["type"] == "image_url"
            assert content[1]["image_url"]["url"].startswith("data:image/jpeg;base64,")

    @pytest.mark.asyncio
    async def test_complete_concurrency_limit(self, client):
        """测试并发限制"""
        messages = [{"role": "user", "content": "Test"}]

        # 创建多个延迟响应
        async def slow_post(*args, **kwargs):
            import asyncio

            await asyncio.sleep(0.1)
            mock_resp = Mock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {
                "choices": [{"message": {"content": "Done"}}]
            }
            return mock_resp

        with patch("httpx.AsyncClient.post", side_effect=slow_post):
            import asyncio

            # 发起 4 个请求，但只有 2 个并发
            tasks = [client.complete(messages, []) for _ in range(4)]
            results = await asyncio.gather(*tasks)

            assert len(results) == 4
            assert all(r == "Done" for r in results)

    @pytest.mark.asyncio
    async def test_complete_http_error(self, client):
        """测试 HTTP 错误处理"""
        messages = [{"role": "user", "content": "Error"}]

        # Mock HTTP 错误
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"

        with patch("httpx.AsyncClient.post", return_value=mock_response):
            with pytest.raises(TableParsingError) as exc_info:
                await client.complete(messages, [])

            assert "500" in str(exc_info.value)
            assert "Internal Server Error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_complete_timeout(self, client):
        """测试超时处理"""
        messages = [{"role": "user", "content": "Timeout"}]

        # Mock 超时异常
        with patch("httpx.AsyncClient.post", side_effect=httpx.TimeoutException("Request timed out")):
            with pytest.raises(TableParsingError) as exc_info:
                await client.complete(messages, [])

            assert "timeout" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_complete_invalid_response(self, client):
        """测试无效响应处理"""
        messages = [{"role": "user", "content": "Invalid"}]

        # Mock 无效响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"invalid": "structure"}

        with patch("httpx.AsyncClient.post", return_value=mock_response):
            with pytest.raises(TableParsingError) as exc_info:
                await client.complete(messages, [])

            assert "Invalid response" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_complete_empty_response(self, client):
        """测试空响应处理"""
        messages = [{"role": "user", "content": "Empty"}]

        # Mock 空响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"choices": []}

        with patch("httpx.AsyncClient.post", return_value=mock_response):
            with pytest.raises(TableParsingError) as exc_info:
                await client.complete(messages, [])

            assert "No choices" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_headers_without_api_key(self):
        """测试无 API key 时的请求头"""
        from table_parsing.config import ModelApiConfig

        config = ModelApiConfig(
            base_url="http://test.local:8000",
            model="test-model",
            api_key="",
        )
        client = OpenAICompatibleClient(config)

        messages = [{"role": "user", "content": "No key"}]

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Response"}}]
        }

        with patch("httpx.AsyncClient.post", return_value=mock_response) as mock_post:
            await client.complete(messages, [])

            # 验证没有 Authorization 头
            headers = mock_post.call_args[1]["headers"]
            assert "Authorization" not in headers

    @pytest.mark.asyncio
    async def test_headers_with_api_key(self, client):
        """测试有 API key 时的请求头"""
        messages = [{"role": "user", "content": "With key"}]

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Response"}}]
        }

        with patch("httpx.AsyncClient.post", return_value=mock_response) as mock_post:
            await client.complete(messages, [])

            # 验证有 Authorization 头
            headers = mock_post.call_args[1]["headers"]
            assert headers["Authorization"] == "Bearer test-key"

    @pytest.mark.asyncio
    async def test_complete_network_error(self, client):
        """测试网络错误处理"""
        messages = [{"role": "user", "content": "Network error"}]

        # Mock 网络错误
        with patch("httpx.AsyncClient.post", side_effect=httpx.ConnectError("Connection failed")):
            with pytest.raises(TableParsingError) as exc_info:
                await client.complete(messages, [])

            assert "Connection failed" in str(exc_info.value)
