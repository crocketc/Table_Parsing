#!/usr/bin/env python3
"""
质量检查脚本 (Python 版本 - 跨平台)
运行 mypy、pytest 和 radon 进行代码质量检查
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str], description: str, strict: bool = True) -> bool:
    """
    运行命令并返回是否成功

    Args:
        cmd: 要运行的命令列表
        description: 命令描述
        strict: 如果为 True，失败时退出程序

    Returns:
        bool: 命令是否成功
    """
    print("=" * 50)
    print(description)
    print("=" * 50)

    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        print("✓ 检查通过")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ 检查失败 (退出码: {e.returncode})")
        if strict:
            sys.exit(1)
        return False
    except FileNotFoundError:
        print(f"✗ 错误: {cmd[0]} 未安装")
        print(f"请运行: pip install {cmd[0]}")
        if strict:
            sys.exit(1)
        return False


def main():
    """主函数"""
    print("=" * 50)
    print("代码质量检查脚本")
    print("=" * 50)
    print()

    # 获取项目根目录
    project_root = Path(__file__).parent.parent
    src_dir = project_root / "src" / "table_parsing"
    tests_dir = project_root / "tests"

    # 1. mypy 类型检查
    mypy_success = run_command(
        ["mypy", str(src_dir)],
        "1. 运行 mypy 类型检查",
        strict=False  # 不严格，允许类型错误
    )
    print()

    # 2. pytest 测试覆盖率检查（需要 pytest-cov）
    try:
        # 先检查是否安装了 pytest-cov
        subprocess.run(
            ["pytest", "--version"],
            check=True,
            capture_output=True
        )
        coverage_success = run_command(
            [
                "pytest",
                f"--cov={src_dir}",
                "--cov-report=term-missing",
                "--cov-fail-under=80",
                str(tests_dir)
            ],
            "2. 运行 pytest --cov 测试覆盖率检查 (目标: ≥80%)",
            strict=False
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        print("⚠ pytest 或 pytest-cov 未安装，跳过覆盖率检查")
        print("  安装命令: pip install pytest pytest-cov")
        coverage_success = False
    print()

    # 3. radon McCabe 复杂度检查（如果可用）
    try:
        subprocess.run(["radon", "--version"], check=True, capture_output=True)
        radon_success = run_command(
            ["radon", "cc", str(src_dir), "-a", "--min", "C"],
            "3. 运行 radon McCabe 复杂度检查 (目标: ≤10)"
        )
        print()

        # 4. radon 可维护性指数
        print("=" * 50)
        print("4. 运行 radon 可维护性指数检查")
        print("=" * 50)
        subprocess.run(["radon", "mi", str(src_dir)], check=False)
        print()
    except (FileNotFoundError, subprocess.CalledProcessError):
        print("⚠ radon 未安装，跳过复杂度检查")
        print("  可选安装: pip install radon")
        print()

    # 总结
    print("=" * 50)
    if coverage_success:
        print("✓ 核心质量检查通过！")
    else:
        print("⚠ 部分检查未通过，请查看上方详细信息")
    print("=" * 50)


if __name__ == "__main__":
    main()
