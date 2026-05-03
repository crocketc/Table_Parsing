"""CLI 工具测试"""
import json
import yaml
from pathlib import Path
from typer.testing import CliRunner

from table_parsing.cli import app

runner = CliRunner()


def test_cli_basic(tmp_path):
    """测试基础 CLI 功能"""
    csv_file = tmp_path / "test.csv"
    csv_file.write_text("A,B,C\n1,2,3\n4,5,6", encoding="utf-8")

    result = runner.invoke(app, ["main", str(csv_file)])

    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["success"] is True
    assert len(data["sheets"]) == 1
    assert data["metadata"]["format"] == "csv"


def test_cli_output_file(tmp_path):
    """测试输出到文件"""
    csv_file = tmp_path / "test.csv"
    csv_file.write_text("A,B,C\n1,2,3", encoding="utf-8")

    output_file = tmp_path / "output.json"

    result = runner.invoke(app, ["main", str(csv_file), "--output", str(output_file)])

    assert result.exit_code == 0
    assert output_file.exists()

    data = json.loads(output_file.read_text(encoding="utf-8"))
    assert data["success"] is True


def test_cli_yaml_format(tmp_path):
    """测试 YAML 输出格式"""
    csv_file = tmp_path / "test.csv"
    csv_file.write_text("A,B,C\n1,2,3", encoding="utf-8")

    result = runner.invoke(app, ["main", str(csv_file), "--format", "yaml"])

    assert result.exit_code == 0
    # 验证是有效的 YAML
    data = yaml.safe_load(result.stdout)
    assert data["success"] is True


def test_cli_csv_format(tmp_path):
    """测试 CSV 输出格式"""
    csv_file = tmp_path / "test.csv"
    csv_file.write_text("A,B,C\n1,2,3\n4,5,6", encoding="utf-8")

    result = runner.invoke(app, ["main", str(csv_file), "--format", "csv"])

    assert result.exit_code == 0
    # 验证输出包含原始数据
    assert "A" in result.stdout
    assert "1" in result.stdout


def test_cli_verbose(tmp_path):
    """测试详细输出模式"""
    csv_file = tmp_path / "test.csv"
    csv_file.write_text("A,B,C\n1,2,3", encoding="utf-8")

    result = runner.invoke(app, ["main", str(csv_file), "--verbose"])

    assert result.exit_code == 0
    # 验证包含详细输出
    assert "解析文件" in result.stdout or "文件大小" in result.stdout


def test_cli_no_file():
    """测试不提供文件时的错误"""
    result = runner.invoke(app, ["main"])

    assert result.exit_code == 1
    assert "请指定要解析的文件" in result.stdout


def test_cli_nonexistent_file():
    """测试不存在的文件"""
    result = runner.invoke(app, ["main", "nonexistent.csv"])

    # Typer 对文件不存在的错误返回退出代码 2
    assert result.exit_code == 2
    # 错误信息可能在 stderr 中
    output = result.stdout + result.stderr
    assert "文件不存在" in output or "No such file" in output or "does not exist" in output


def test_cli_init_config(tmp_path):
    """测试生成配置文件"""
    import os
    original_cwd = os.getcwd()

    try:
        # 切换到临时目录
        os.chdir(tmp_path)
        result = runner.invoke(app, ["main", "--init-config"])

        assert result.exit_code == 0
        assert "已创建配置文件" in result.stdout
        assert (tmp_path / ".table-parse.yml").exists()
    finally:
        os.chdir(original_cwd)


def test_cli_show_config(tmp_path, sample_config):
    """测试显示配置"""
    result = runner.invoke(app, ["main", "--show-config"])

    assert result.exit_code == 0
    assert "当前配置" in result.stdout


def test_cli_show_config_path_with_config(tmp_path):
    """测试显示配置文件路径（有配置文件）"""
    config_file = tmp_path / ".table-parse.yml"
    config_file.write_text("output_format: yaml\n", encoding="utf-8")

    result = runner.invoke(app, ["main", "--show-config-path"])

    assert result.exit_code == 0
    assert ".table-parse.yml" in result.stdout


def test_cli_show_config_path_without_config(tmp_path):
    """测试显示配置文件路径（无配置文件）"""
    # 切换到临时目录，确保没有配置文件
    import os
    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        result = runner.invoke(app, ["main", "--show-config-path"])

        assert result.exit_code == 0
        assert "未找到配置文件" in result.stdout
    finally:
        os.chdir(original_cwd)


def test_cli_config_file_override(tmp_path):
    """测试配置文件覆盖"""
    # 创建配置文件
    config_file = tmp_path / ".table-parse.yml"
    config_file.write_text("output_format: yaml\npretty: false\n", encoding="utf-8")

    csv_file = tmp_path / "test.csv"
    csv_file.write_text("A,B,C\n1,2,3", encoding="utf-8")

    result = runner.invoke(app, ["main", str(csv_file)])

    assert result.exit_code == 0
    # YAML 格式应该有特定输出
    data = yaml.safe_load(result.stdout)
    assert data["success"] is True


def test_cli_cli_arg_override(tmp_path):
    """测试命令行参数覆盖配置文件"""
    # 创建配置文件指定 yaml 格式
    config_file = tmp_path / ".table-parse.yml"
    config_file.write_text("output_format: yaml\n", encoding="utf-8")

    csv_file = tmp_path / "test.csv"
    csv_file.write_text("A,B,C\n1,2,3", encoding="utf-8")

    # 命令行指定 json 格式，应该覆盖配置文件
    result = runner.invoke(app, ["main", str(csv_file), "--format", "json"])

    assert result.exit_code == 0
    # 应该是 JSON 格式，不是 YAML
    data = json.loads(result.stdout)
    assert data["success"] is True
