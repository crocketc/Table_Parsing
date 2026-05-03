"""
CLI 配置文件处理模块

提供配置文件的查找、加载、合并和验证功能。
"""

from pathlib import Path
from typing import Any, Dict, Optional, List
import yaml


def find_config_file(config_path: Optional[Path] = None) -> Optional[Path]:
    """
    查找配置文件

    查找顺序：
    1. 命令行 --config 指定的文件
    2. 当前目录的 .table-parse.yml
    3. 当前目录的 table-parse.yml
    4. 用户主目录的 .table-parse.yml
    5. 用户主目录的 .config/table-parse/config.yml

    Args:
        config_path: 命令行指定的配置文件路径

    Returns:
        找到的配置文件路径，如果未找到则返回 None
    """
    if config_path:
        if config_path.exists():
            return config_path
        return None

    candidates = [
        Path.cwd() / ".table-parse.yml",
        Path.cwd() / "table-parse.yml",
        Path.home() / ".table-parse.yml",
        Path.home() / ".config" / "table-parse" / "config.yml",
    ]

    for path in candidates:
        if path.exists():
            return path

    return None


def load_config_file(config_path: Path) -> Dict[str, Any]:
    """
    加载 YAML 配置文件

    Args:
        config_path: 配置文件路径

    Returns:
        解析后的配置字典
    """
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    except yaml.YAMLError as e:
        raise ValueError(f"配置文件格式错误: {e}")
    except Exception as e:
        raise ValueError(f"加载配置文件失败: {e}")


def get_default_config() -> Dict[str, Any]:
    """
    获取系统默认配置

    Returns:
        默认配置字典
    """
    return {
        "encoding": None,
        "extract_media": True,
        "sheets": None,
        "range": None,
        "output_format": "json",
        "pretty": True,
        "verbose": False,
        "model_api": {
            "base_url": "http://169.254.83.107:1234",
            "model": "qwen3.5-4b",
            "api_key": "",
            "max_concurrency": 6,
        },
        "log_level": "INFO",
    }


def merge_config(
    file_config: Dict[str, Any],
    cli_args: Dict[str, Any],
    default_config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    合并配置：命令行参数 > 配置文件 > 默认值

    Args:
        file_config: 从配置文件加载的配置
        cli_args: 命令行参数
        default_config: 系统默认配置

    Returns:
        合并后的配置字典
    """
    if default_config is None:
        default_config = get_default_config()

    result = default_config.copy()

    for key in file_config:
        if isinstance(file_config[key], dict) and key in result and isinstance(result[key], dict):
            result[key] = {**result[key], **file_config[key]}
        else:
            result[key] = file_config[key]

    for key in cli_args:
        if cli_args[key] is not None:
            if isinstance(cli_args[key], dict) and key in result and isinstance(result[key], dict):
                result[key] = {**result[key], **cli_args[key]}
            else:
                result[key] = cli_args[key]

    return result


def validate_config(config: Dict[str, Any]) -> List[str]:
    """
    验证配置

    Args:
        config: 要验证的配置字典

    Returns:
        错误信息列表，如果为空则表示配置有效
    """
    errors = []

    # 验证输出格式（仅当明确指定时）
    output_format = config.get("output_format")
    if output_format is not None:
        valid_formats = ["json", "yaml", "csv"]
        if output_format not in valid_formats:
            errors.append(f"无效的输出格式: {output_format}，支持的格式: {', '.join(valid_formats)}")

    # 验证日志级别（仅当明确指定时）
    log_level = config.get("log_level")
    if log_level is not None:
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR"]
        if log_level not in valid_log_levels:
            errors.append(f"无效的日志级别: {log_level}，支持的级别: {', '.join(valid_log_levels)}")

    # 验证编码（仅当明确指定时）
    encoding = config.get("encoding")
    if encoding is not None:
        try:
            "test".encode(encoding)
        except LookupError:
            errors.append(f"不支持的编码: {encoding}")

    return errors


def create_config_template(output_path: Path) -> None:
    """
    创建配置文件模板

    Args:
        output_path: 输出文件路径
    """
    template = """# 表格解析 CLI 配置文件
# 复制此文件为 .table-parse.yml 并根据需要修改

# 文件编码（留空表示自动检测）
encoding: null

# 是否提取嵌入的媒体文件
extract_media: true

# 指定要解析的工作表（留空表示解析所有）
sheets: null
# sheets:
#   - "Sheet1"
#   - "Sheet2"

# 解析范围（如 "A1:B10"）
range: null

# 输出格式：json/yaml/csv
output_format: json

# 是否格式化输出
pretty: true

# 模型 API 配置
model_api:
  base_url: "http://169.254.83.107:1234"
  model: "qwen3.5-4b"
  api_key: ""
  max_concurrency: 6

# 日志级别：DEBUG/INFO/WARNING/ERROR
log_level: "INFO"
"""

    output_path.write_text(template, encoding='utf-8')


def show_config(config: Dict[str, Any]) -> str:
    """
    格式化显示配置

    Args:
        config: 配置字典

    Returns:
        格式化后的配置字符串
    """
    return yaml.dump(config, allow_unicode=True, sort_keys=False)
