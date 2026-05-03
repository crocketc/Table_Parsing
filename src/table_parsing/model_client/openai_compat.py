"""OpenAI Chat Completions API 兼容客户端"""

import asyncio
import base64
import logging
from io import BytesIO
from typing import List

import httpx
from PIL import Image

from ..config import ModelApiConfig
from ..exceptions import TableParsingError
from .base import ModelClient

logger = logging.getLogger(__name__)


class OpenAICompatibleClient(ModelClient):
    """
    OpenAI Chat Completions API 兼容的 HTTP 客户端

    支持同步和异步调用，兼容 OpenAI Chat Completions 格式。
    适用于 LM Studio、Ollama、vLLM、Azure OpenAI 等服务。

    Args:
        config: 模型 API 配置

    Features:
    - 异步 HTTP 调用，基于 httpx
    - 并发控制，使用 asyncio.Semaphore
    - 自动处理图片编码（base64）
    - 灵活的 API Key 处理（空值时不发送 Authorization 头）
    """

    def __init__(self, config: ModelApiConfig):
        """
        初始化客户端

        Args:
            config: 模型 API 配置
        """
        self._base_url = config.base_url
        self._model = config.model
        self._api_key = config.api_key
        self._max_concurrency = config.max_concurrency
        self._semaphore = asyncio.Semaphore(config.max_concurrency)
        self._timeout = 30.0  # 30 秒超时

    async def complete(self, messages: List[dict], images: List[bytes]) -> str:
        """
        调用模型进行多模态完成

        Args:
            messages: 对话消息列表
            images: 图片字节数据列表

        Returns:
            模型生成的响应文本

        Raises:
            TableParsingError: API 调用失败时抛出
        """
        async with self._semaphore:
            try:
                return await self._do_complete(messages, images)
            except (httpx.TimeoutException, asyncio.TimeoutError) as e:
                logger.error(f"Model API timeout: {e}")
                raise TableParsingError(f"Model API timeout: {e}") from e
            except httpx.HTTPStatusError as e:
                logger.error(f"Model API HTTP error: {e.response.status_code}")
                raise TableParsingError(
                    f"Model API error: {e.response.status_code} - {e.response.text}"
                ) from e
            except httpx.ConnectError as e:
                logger.error(f"Model API connection error: {e}")
                raise TableParsingError(f"Model API connection failed: {e}") from e
            except Exception as e:
                logger.error(f"Model API unexpected error: {e}")
                raise TableParsingError(f"Model API error: {e}") from e

    async def _do_complete(self, messages: List[dict], images: List[bytes]) -> str:
        """
        执行实际的 API 调用

        Args:
            messages: 对话消息列表
            images: 图片字节数据列表

        Returns:
            模型生成的响应文本
        """
        # 构建请求 URL
        url = f"{self._base_url.rstrip('/')}/v1/chat/completions"

        # 构建请求头
        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"

        # 构建请求体
        request_messages = self._build_messages(messages, images)

        request_data = {
            "model": self._model,
            "messages": request_messages,
            "max_tokens": 4096,
        }

        logger.debug(f"Sending request to {url}")

        # 发送 HTTP 请求
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json=request_data,
                headers=headers,
                timeout=self._timeout,
            )

            # 检查 HTTP 状态码
            if response.status_code != 200:
                raise httpx.HTTPStatusError(
                    f"HTTP {response.status_code}: {response.text}",
                    request=response.request,
                    response=response,
                )

            # 解析响应
            response_data = response.json()

            # 验证响应格式
            if "choices" not in response_data:
                raise TableParsingError(f"Invalid response format: {response_data}")

            if not response_data["choices"]:
                raise TableParsingError("No choices in response")

            # 提取生成的文本
            content = response_data["choices"][0]["message"]["content"]

            # 类型断言：确保 content 是字符串
            if not isinstance(content, str):
                raise TableParsingError(f"Invalid response content type: {type(content)}")

            logger.debug(f"Received response: {len(content)} chars")

            return content

    def _build_messages(self, messages: List[dict], images: List[bytes]) -> List[dict]:
        """
        构建包含图片的消息列表

        Args:
            messages: 原始消息列表
            images: 图片字节数据列表

        Returns:
            构建后的消息列表
        """
        if not images:
            # 没有图片，直接返回原消息
            return messages

        # 有图片，将图片编码到消息中
        built_messages = []

        for msg in messages:
            built_msg = {"role": msg["role"], "content": []}

            # 添加文本内容
            built_msg["content"].append({
                "type": "text",
                "text": msg["content"],
            })

            # 添加图片内容
            for img_bytes in images:
                img_format = self._detect_image_format(img_bytes)
                img_b64 = base64.b64encode(img_bytes).decode()

                built_msg["content"].append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/{img_format};base64,{img_b64}",
                    },
                })

            built_messages.append(built_msg)

        return built_messages

    def _detect_image_format(self, img_bytes: bytes) -> str:
        """
        检测图片格式

        Args:
            img_bytes: 图片字节数据

        Returns:
            图片格式（png、jpeg 等）
        """
        try:
            img = Image.open(BytesIO(img_bytes))
            format_lower = img.format.lower() if img.format else "png"

            # 统一格式名称
            if format_lower == "jpg":
                return "jpeg"
            return format_lower
        except Exception:
            # 默认返回 png
            return "png"
