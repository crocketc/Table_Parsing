#!/usr/bin/env python3
"""
Table Parsing IR - 命令行工具

用法：
    table-parse data.csv
    table-parse report.xlsx --output result.json
    table-parse data.xlsx --config my-config.yml --sheet "Sheet1"
"""

import json
import sys
from pathlib import Path
from typing import Optional, List

import typer
from rich.console import Console
from rich.syntax import Syntax

from . import parse_file, __version__
from .exceptions import TableParsingError
from .cli_config import (
    find_config_file,
    load_config_file,
    get_default_config,
    merge_config,
    validate_config,
    create_config_template,
    show_config,
)

app = typer.Typer(
    name="table-parse",
    help="表格文件解析工具 - 支持 CSV/XLS/XLSX 格式",
    add_completion=False,
)

console = Console()


@app.command()
def main(
    file: Optional[Path] = typer.Argument(
        None,
        exists=True,
        help="要解析的表格文件路径",
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output", "-o",
        help="输出文件路径（默认输出到 stdout）",
    ),
    config: Optional[Path] = typer.Option(
        None,
        "--config", "-c",
        help="配置文件路径",
    ),
    format: Optional[str] = typer.Option(
        None,
        "--format", "-f",
        help="输出格式：json/yaml/csv",
    ),
    sheet: Optional[List[str]] = typer.Option(
        None,
        "--sheet", "-s",
        help="指定要解析的工作表名称（可多次使用）",
    ),
    range: Optional[str] = typer.Option(
        None,
        "--range", "-r",
        help="解析范围（如 A1:B10）",
    ),
    encoding: Optional[str] = typer.Option(
        None,
        "--encoding", "-e",
        help="文件编码（如 utf-8/gbk）",
    ),
    extract_media: Optional[bool] = typer.Option(
        None,
        "--extract-media/--no-extract-media",
        help="是否提取嵌入的媒体文件",
    ),
    verbose: Optional[bool] = typer.Option(
        None,
        "--verbose", "-v",
        help="显示详细输出",
    ),
    pretty: Optional[bool] = typer.Option(
        None,
        "--pretty/--no-pretty",
        help="格式化 JSON 输出",
    ),
    init_config: bool = typer.Option(
        False,
        "--init-config",
        help="在当前目录生成配置文件模板",
    ),
    show_config_flag: bool = typer.Option(
        False,
        "--show-config",
        help="显示当前生效的配置",
    ),
    show_config_path: bool = typer.Option(
        False,
        "--show-config-path",
        help="显示配置文件路径",
    ),
) -> None:
    """
    解析表格文件并输出结果

    示例：
        table-parse data.csv
        table-parse report.xlsx -o result.json
        table-parse data.xlsx -s "Sheet1" -f yaml
    """
    try:
        # 处理特殊命令
        if init_config:
            config_file = Path.cwd() / ".table-parse.yml"
            create_config_template(config_file)
            console.print(f"[bold green]✅[/bold green] 已创建配置文件: [bold blue]{config_file}[/bold blue]")
            console.print("[yellow]📝[/yellow] 请根据需要修改配置")
            return

        if show_config_path:
            config_file = find_config_file(config)
            if config_file:
                console.print(f"[bold blue]配置文件:[/bold blue] {config_file}")
            else:
                console.print("[yellow]未找到配置文件[/yellow]")
            return

        # 加载配置
        config_file = find_config_file(config)
        file_config = {}
        if config_file:
            file_config = load_config_file(config_file)

        # 命令行参数
        cli_args = {}
        if format is not None:
            cli_args["output_format"] = format
        if sheet is not None:
            cli_args["sheets"] = sheet
        if range is not None:
            cli_args["range"] = range
        if encoding is not None:
            cli_args["encoding"] = encoding
        if extract_media is not None:
            cli_args["extract_media"] = extract_media
        if verbose is not None:
            cli_args["verbose"] = verbose
        if pretty is not None:
            cli_args["pretty"] = pretty

        # 合并配置
        merged_config = merge_config(file_config, cli_args)

        # 验证配置
        errors = validate_config(merged_config)
        if errors:
            console.print("[bold red]配置错误:[/bold red]")
            for error in errors:
                console.print(f"  - {error}")
            raise typer.Exit(code=1)

        if show_config_flag:
            console.print("[bold blue]当前配置:[/bold blue]")
            console.print(Syntax(show_config(merged_config), "yaml", theme="monokai"))
            if config_file:
                console.print(f"[dim]配置文件: {config_file}[/dim]")
            return

        # 检查文件参数
        if file is None:
            console.print("[bold red]错误:[/bold red] 请指定要解析的文件")
            console.print("使用 --help 查看帮助")
            raise typer.Exit(code=1)

        # 显示解析信息
        if merged_config.get("verbose"):
            console.print(f"[bold blue]解析文件:[/bold blue] {file}")
            console.print(f"[bold blue]文件大小:[/bold blue] {file.stat().st_size:,} bytes")
            if config_file:
                console.print(f"[bold blue]配置文件:[/bold blue] {config_file}")

        # 解析文件（使用默认配置）
        workbook = parse_file(file)

        # 过滤工作表
        if merged_config.get("sheets"):
            workbook.sheets = [s for s in workbook.sheets if s.name in merged_config["sheets"]]

        # 转换为字典
        result = {
            "success": True,
            "metadata": {
                "filename": file.name,
                "format": file.suffix.lstrip('.'),
                "sheets_count": len(workbook.sheets),
                "file_size_bytes": file.stat().st_size,
            },
            "sheets": [s.to_dict() for s in workbook.sheets],
        }

        # 输出结果
        output_format = merged_config.get("output_format", "json")
        pretty = merged_config.get("pretty", True)
        output_data = _format_output(result, output_format, pretty)

        if output:
            # 写入文件
            output.write_text(output_data, encoding="utf-8")
            if merged_config.get("verbose"):
                console.print(f"[bold green]✅ 结果已保存:[/bold green] {output}")
        else:
            # 输出到 stdout
            if output_format == "json" and pretty:
                console.print_json(output_data)
            else:
                console.print(output_data)

    except FileNotFoundError as e:
        console.print(f"[bold red]错误:[/bold red] 文件不存在: {e}")
        raise typer.Exit(code=1)
    except TableParsingError as e:
        console.print(f"[bold red]解析错误:[/bold red] {e}")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[bold red]未知错误:[/bold red] {e}")
        raise typer.Exit(code=1)


def _format_output(result: dict, format: str, pretty: bool) -> str:
    """格式化输出"""
    if format == "json":
        if pretty:
            return json.dumps(result, ensure_ascii=False, indent=2)
        return json.dumps(result, ensure_ascii=False)
    elif format == "yaml":
        try:
            import yaml
            return yaml.dump(result, allow_unicode=True, sort_keys=False)
        except ImportError:
            console.print("[bold yellow]⚠️[/bold yellow] YAML 格式需要安装 PyYAML")
            console.print("  安装: pip install pyyaml")
            return json.dumps(result, ensure_ascii=False, indent=2)
    elif format == "csv":
        import csv
        import io

        output = io.StringIO()
        sheets = result.get("sheets", [])
        if sheets:
            sheet = sheets[0]
            cells = sheet.get("cells", [])
            writer = csv.writer(output)
            for row in cells:
                writer.writerow([cell.get("value", "") for cell in row])
        return output.getvalue()
    else:
        console.print(f"[bold yellow]⚠️[/bold yellow] 未知格式: {format}")
        return json.dumps(result, ensure_ascii=False, indent=2)


@app.command()
def version() -> None:
    """显示版本信息"""
    console.print(f"table-parse version {__version__}")


if __name__ == "__main__":
    app()
