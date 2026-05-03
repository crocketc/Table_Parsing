"""CLI 配置文件处理模块测试"""
import yaml
from pathlib import Path
import pytest

from table_parsing.cli_config import (
    find_config_file,
    load_config_file,
    get_default_config,
    merge_config,
    validate_config,
    create_config_template,
    show_config,
)


def test_get_default_config():
    """测试获取默认配置"""
    config = get_default_config()

    assert config["extract_media"] is True
    assert config["output_format"] == "json"
    assert config["pretty"] is True
    assert config["model_api"]["base_url"] == "http://169.254.83.107:1234"
    assert config["model_api"]["model"] == "qwen3.5-4b"


def test_find_config_file_specified(tmp_path):
    """测试查找指定的配置文件"""
    config_file = tmp_path / "my-config.yml"
    config_file.write_text("output_format: yaml\n", encoding="utf-8")

    result = find_config_file(config_file)

    assert result == config_file


def test_find_config_file_current_dir(tmp_path):
    """测试查找当前目录的配置文件"""
    config_file = tmp_path / ".table-parse.yml"
    config_file.write_text("output_format: yaml\n", encoding="utf-8")

    import os
    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        result = find_config_file()
        assert result == config_file
    finally:
        os.chdir(original_cwd)


def test_find_config_file_not_found(tmp_path):
    """测试找不到配置文件的情况"""
    import os
    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        result = find_config_file()
        assert result is None
    finally:
        os.chdir(original_cwd)


def test_load_config_file(tmp_path):
    """测试加载配置文件"""
    config_file = tmp_path / "config.yml"
    config_content = """
output_format: yaml
pretty: false
encoding: utf-8
"""
    config_file.write_text(config_content, encoding="utf-8")

    config = load_config_file(config_file)

    assert config["output_format"] == "yaml"
    assert config["pretty"] is False
    assert config["encoding"] == "utf-8"


def test_load_config_file_empty(tmp_path):
    """测试加载空配置文件"""
    config_file = tmp_path / "config.yml"
    config_file.write_text("", encoding="utf-8")

    config = load_config_file(config_file)

    assert config == {}


def test_load_config_file_invalid(tmp_path):
    """测试加载无效的配置文件"""
    config_file = tmp_path / "config.yml"
    config_file.write_text("invalid: yaml: content:\n  -", encoding="utf-8")

    with pytest.raises(ValueError, match="配置文件格式错误"):
        load_config_file(config_file)


def test_merge_config():
    """测试配置合并"""
    default = {"a": 1, "b": 2, "nested": {"x": 10, "y": 20}}
    file_config = {"b": 3, "nested": {"y": 30}}
    cli_args = {"c": 4, "nested": {"z": 40}}

    result = merge_config(file_config, cli_args, default)

    assert result["a"] == 1  # 默认值
    assert result["b"] == 3  # 配置文件覆盖
    assert result["c"] == 4  # 命令行参数
    assert result["nested"]["x"] == 10  # 默认值
    assert result["nested"]["y"] == 30  # 配置文件覆盖
    assert result["nested"]["z"] == 40  # 命令行参数


def test_merge_config_cli_overrides_file():
    """测试命令行参数覆盖配置文件"""
    default = {"format": "json"}
    file_config = {"format": "yaml"}
    cli_args = {"format": "csv"}

    result = merge_config(file_config, cli_args, default)

    assert result["format"] == "csv"


def test_validate_config_valid():
    """测试验证有效配置"""
    config = {
        "output_format": "json",
        "log_level": "INFO",
        "encoding": "utf-8",
    }

    errors = validate_config(config)

    assert len(errors) == 0


def test_validate_config_invalid_format():
    """测试验证无效的输出格式"""
    config = {"output_format": "xml"}

    errors = validate_config(config)

    assert len(errors) > 0
    assert "输出格式" in errors[0]


def test_validate_config_invalid_log_level():
    """测试验证无效的日志级别"""
    config = {"log_level": "TRACE"}

    errors = validate_config(config)

    assert len(errors) > 0
    assert "日志级别" in errors[0]


def test_validate_config_invalid_encoding():
    """测试验证无效的编码"""
    config = {"encoding": "invalid-encoding-xyz"}

    errors = validate_config(config)

    assert len(errors) > 0
    assert "编码" in errors[0]


def test_create_config_template(tmp_path):
    """测试创建配置文件模板"""
    output_path = tmp_path / "test-config.yml"

    create_config_template(output_path)

    assert output_path.exists()

    content = output_path.read_text(encoding="utf-8")
    assert "output_format:" in content
    assert "model_api:" in content

    # 验证是有效的 YAML
    config = yaml.safe_load(content)
    assert "extract_media" in config


def test_show_config():
    """测试格式化显示配置"""
    config = {
        "output_format": "json",
        "pretty": True,
        "nested": {"key": "value"},
    }

    result = show_config(config)

    assert isinstance(result, str)
    assert "output_format" in result
    assert "nested" in result

    # 验证是有效的 YAML
    loaded = yaml.safe_load(result)
    assert loaded["output_format"] == "json"
