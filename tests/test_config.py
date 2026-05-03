"""测试配置数据类"""

import pytest

from table_parsing.config import ModelApiConfig, ParseConfig


class TestModelApiConfig:
    """测试 ModelApiConfig 数据类"""

    def test_model_api_config_defaults(self):
        """测试 ModelApiConfig 的默认值"""
        config = ModelApiConfig()

        assert config.base_url == "http://169.254.83.107:1234"
        assert config.model == "qwen3.5-4b"
        assert config.api_key == ""
        assert config.max_concurrency == 6

    def test_model_api_config_custom_values(self):
        """测试自定义 ModelApiConfig 值"""
        config = ModelApiConfig(
            base_url="http://custom.url:8080",
            model="custom-model",
            api_key="sk-test-key",
            max_concurrency=10,
        )

        assert config.base_url == "http://custom.url:8080"
        assert config.model == "custom-model"
        assert config.api_key == "sk-test-key"
        assert config.max_concurrency == 10

    def test_model_api_config_partial_custom(self):
        """测试部分自定义 ModelApiConfig 值"""
        config = ModelApiConfig(model="other-model", max_concurrency=3)

        assert config.base_url == "http://169.254.83.107:1234"  # 默认值
        assert config.model == "other-model"
        assert config.api_key == ""  # 默认值
        assert config.max_concurrency == 3


class TestParseConfig:
    """测试 ParseConfig 数据类"""

    def test_parse_config_defaults(self):
        """测试 ParseConfig 的默认值"""
        config = ParseConfig()

        assert config.encoding is None
        assert config.encoding_detection is True
        assert config.extract_media is True  # 默认值实际为 True
        assert config.chunk_size is None
        assert config.sheets is None
        assert config.range is None
        assert isinstance(config.model_api, ModelApiConfig)
        assert config.model_api.base_url == "http://169.254.83.107:1234"

    def test_parse_config_custom_values(self):
        """测试自定义 ParseConfig 值"""
        model_api = ModelApiConfig(
            base_url="http://test.com:9999",
            model="test-model",
            api_key="test-key",
            max_concurrency=5,
        )

        config = ParseConfig(
            encoding="utf-8",
            encoding_detection=False,
            extract_media=True,
            chunk_size=1000,
            sheets=["Sheet1", "Sheet2"],
            range="A1:Z100",
            model_api=model_api,
        )

        assert config.encoding == "utf-8"
        assert config.encoding_detection is False
        assert config.extract_media is True
        assert config.chunk_size == 1000
        assert config.sheets == ["Sheet1", "Sheet2"]
        assert config.range == "A1:Z100"
        assert config.model_api.base_url == "http://test.com:9999"
        assert config.model_api.model == "test-model"
        assert config.model_api.api_key == "test-key"
        assert config.model_api.max_concurrency == 5

    def test_parse_config_partial_custom(self):
        """测试部分自定义 ParseConfig 值"""
        config = ParseConfig(encoding="gbk", extract_media=True)

        assert config.encoding == "gbk"
        assert config.encoding_detection is True  # 默认值
        assert config.extract_media is True
        assert config.chunk_size is None  # 默认值
        assert config.sheets is None  # 默认值
        assert config.range is None  # 默认值
        assert isinstance(config.model_api, ModelApiConfig)

    def test_parse_config_default_model_api(self):
        """测试不提供 model_api 时使用默认值"""
        config = ParseConfig()

        assert config.model_api.base_url == "http://169.254.83.107:1234"
        assert config.model_api.model == "qwen3.5-4b"
        assert config.model_api.api_key == ""
        assert config.model_api.max_concurrency == 6

    def test_parse_config_custom_model_api_via_dict(self):
        """测试通过字典参数自定义 model_api"""
        config = ParseConfig(
            model_api=ModelApiConfig(
                base_url="http://example.com:5555",
                model="gpt-4",
                api_key="sk-12345",
                max_concurrency=8,
            )
        )

        assert config.model_api.base_url == "http://example.com:5555"
        assert config.model_api.model == "gpt-4"
        assert config.model_api.api_key == "sk-12345"
        assert config.model_api.max_concurrency == 8
