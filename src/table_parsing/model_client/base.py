"""模型 API 客户端协议"""

from typing import List, Protocol


class ModelClient(Protocol):
    """
    多模态模型 API 客户端协议

    定义了与多模态大模型交互的标准接口，支持文本和图片输入。
    """

    async def complete(self, messages: List[dict], images: List[bytes]) -> str:
        """
        调用模型进行多模态完成

        Args:
            messages: 对话消息列表，每个消息是包含 role 和 content 的字典
            images: 图片字节数据列表

        Returns:
            模型生成的响应文本

        Raises:
            TableParsingError: API 调用失败时抛出

        Examples:
            >>> client = ModelClient()
            >>> messages = [{"role": "user", "content": "这是什么？"}]
            >>> with open("image.png", "rb") as f:
            ...     img_bytes = f.read()
            >>> response = await client.complete(messages, [img_bytes])
        """
        ...
