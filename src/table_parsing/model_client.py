"""模型 API 客户端"""

import base64
import io
from typing import List, Optional, Protocol

import httpx
from PIL import Image

from .config import ModelApiConfig
from .exceptions import TableParsingError


class ModelClient(Protocol):
    """模型客户端协议

    定义所有模型客户端必须实现的接口。
    """

    async def complete(
        self, messages: List[dict], images: List[bytes]
    ) -> str:
        """完成聊天请求

        Args:
            messages: 聊天消息列表
            images: 图片字节数组

        Returns:
            模型响应文本

        Raises:
            TableParsingError: 请求失败时抛出
        """
        ...


class OpenAICompatibleClient:
    """OpenAI 兼容 API 客户端

    实现与 OpenAI API 兼容的 HTTP 客户端，支持：
    - 异步请求
    - 并发控制（基于信号量）
    - 图片 Base64 编码
    - 可选 API key
    - 30 秒超时
    """

    def __init__(self, config: ModelApiConfig) -> None:
        """初始化客户端

        Args:
            config: 模型 API 配置
        """
        self._base_url = config.base_url
        self._model = config.model
        self._api_key = config.api_key
        self._max_concurrency = config.max_concurrency
        self._semaphore: Optional[httpx._transports.base.Semaphore] = None

    async def complete(
        self, messages: List[dict], images: List[bytes]
    ) -> str:
        """完成聊天请求

        Args:
            messages: 聊天消息列表，格式为 [{"role": "user", "content": "..."}]
            images: 图片字节数组

        Returns:
            模型响应文本

        Raises:
            TableParsingError: HTTP 错误、超时或无效响应时抛出
        """
        import asyncio

        # 延迟创建信号量，确保在事件循环中
        if self._semaphore is None:
            self._semaphore = asyncio.Semaphore(self._max_concurrency)

        async with self._semaphore:
            return await self._do_complete(messages, images)

    async def _do_complete(
        self, messages: List[dict], images: List[bytes]
    ) -> str:
        """执行实际的 HTTP 请求

        Args:
            messages: 聊天消息列表
            images: 图片字节数组

        Returns:
            模型响应文本

        Raises:
            TableParsingError: 请求失败时抛出
        """
        # 构建请求内容
        content = self._build_content(messages[0]["content"], images)
        request_messages = [{"role": messages[0]["role"], "content": content}]

        # 构建请求头
        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"

        # 构建请求体
        request_data = {
            "model": self._model,
            "messages": request_messages,
            "max_tokens": 4096,
        }

        url = f"{self._base_url}/v1/chat/completions"

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    url,
                    json=request_data,
                    headers=headers,
                )

                if response.status_code != 200:
                    raise TableParsingError(
                        f"API request failed with status {response.status_code}: "
                        f"{response.text}"
                    )

                data = response.json()

                # 验证响应结构
                if "choices" not in data:
                    raise TableParsingError(
                        f"Invalid response format: 'choices' field missing. "
                        f"Response: {data}"
                    )

                if not data["choices"]:
                    raise TableParsingError(
                        f"Invalid response format: 'choices' is empty. "
                        f"Response: {data}"
                    )

                return data["choices"][0]["message"]["content"]

        except httpx.TimeoutException as e:
            raise TableParsingError(f"Request timeout: {e}") from e
        except httpx.HTTPError as e:
            raise TableParsingError(f"HTTP error: {e}") from e
        except Exception as e:
            if isinstance(e, TableParsingError):
                raise
            raise TableParsingError(f"Unexpected error: {e}") from e

    def _build_content(self, text: str, images: List[bytes]) -> dict | list:
        """构建请求内容

        Args:
            text: 文本内容
            images: 图片字节数组

        Returns:
            内容结构（纯文本时返回字符串，有图片时返回列表）
        """
        if not images:
            return text

        # 有图片时，构建多模态内容
        content = [{"type": "text", "text": text}]

        for img_bytes in images:
            # 检测图片格式
            img = Image.open(io.BytesIO(img_bytes))
            format_lower = img.format.lower() if img.format else "png"

            # Base64 编码
            img_b64 = base64.b64encode(img_bytes).decode("utf-8")
            img_url = f"data:image/{format_lower};base64,{img_b64}"

            content.append({"type": "image_url", "image_url": {"url": img_url}})

        return content
