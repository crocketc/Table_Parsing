"""配置数据类"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ModelApiConfig:
    """模型 API 配置"""

    base_url: str = "http://169.254.83.107:1234"
    model: str = "qwen3.5-4b"
    api_key: str = ""
    max_concurrency: int = 6


@dataclass
class ParseConfig:
    """解析配置"""

    encoding: Optional[str] = None
    encoding_detection: bool = True
    extract_media: bool = False
    chunk_size: Optional[int] = None
    sheets: Optional[List[str]] = None
    range: Optional[str] = None
    model_api: ModelApiConfig = field(default_factory=ModelApiConfig)
